"""Underwrite — FastAPI Application Server (app.py)

Event-Driven Architecture:
- POST /evaluate returns HTTP 200 OK immediately to client.
- Schedules process_verdict_writeback_event as a non-blocking BackgroundTask.
- Enforces Invariant 4: Verdict generation and UI rendering NEVER depend on write-back.
"""

import json
import logging
from datetime import datetime, timezone
from pathlib import Path

from fastapi import BackgroundTasks, FastAPI, Header, HTTPException, status
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field, field_validator

from agent import Agent, InternalGraph, VerdictInternal, load_policies_from_yaml
from config import settings
from constants import ReasonCode, Verdict
from exceptions import UnderwriteError, PolicyConfigurationError
from metadata.client import DataHubClient
from datahub_client import DataHubWriteBackClient, process_verdict_writeback_event, create_datahub_client
from remediation.advisor import RemediationContext, generate, DISCLAIMER
from collections import OrderedDict

class DecisionStore:
    def __init__(self, max_size: int = 256):
        self._items = OrderedDict()
        self._max_size = max_size

    def put(self, decision_id: str, context: RemediationContext) -> None:
        self._items[decision_id] = context
        self._items.move_to_end(decision_id)

        while len(self._items) > self._max_size:
            self._items.popitem(last=False)

    def get(self, decision_id: str) -> RemediationContext | None:
        return self._items.get(decision_id)

decision_store = DecisionStore()

logger = logging.getLogger("underwrite.server")

# Fail-closed policy configuration at startup
GLOBAL_POLICIES = load_policies_from_yaml(settings.policy_path)

app = FastAPI(
    title="Underwrite",
    description="The signature a model needs before it's allowed to exist in production.",
)

BASE_DIR = Path(__file__).parent
STATIC_DIR = BASE_DIR / "web" / "static"
CACHE_DIR = BASE_DIR / "cache"


def get_metadata_client() -> DataHubClient | None:
    """Instantiate and test DataHubClient connection."""
    try:
        client = create_datahub_client(settings)
        return client if client.is_healthy() else None
    except Exception as e:
        logger.warning(
            "DataHub GMS unavailable (%s); authorization will fail closed",
            e,
        )
        return None


class EvaluateRequest(BaseModel):
    model_urn: str = Field(..., description="Canonical DataHub ML Model URN")
    environment: str = Field(default="PROD", description="Target environment for the deployment")
    action: str = Field(default="DEPLOY", description="Requested authorization action")
    requested_by: str = Field(default="urn:li:corpuser:unknown", description="Principal requesting the action")

    @field_validator("model_urn")
    @classmethod
    def validate_model_urn(cls, value: str) -> str:
        if not value.startswith("urn:li:mlModel:("):
            raise ValueError("model_urn must be a canonical DataHub ML Model URN")
        return value


class OverrideRequest(BaseModel):
    model_urn: str
    signer_name: str = Field(..., min_length=1, max_length=256)

    @field_validator("model_urn")
    @classmethod
    def validate_model_urn(cls, value: str) -> str:
        if not value.startswith("urn:li:mlModel:("):
            raise ValueError("model_urn must be a canonical DataHub ML Model URN")
        return value


def graph_to_ui_payload(graph: InternalGraph, verdict: VerdictInternal) -> dict:
    """Serialize the graph acquired for this evaluation for the UI."""
    type_map = {
        "mlModel": "model",
        "mlFeature": "feature",
        "dataset": "dataset",
        "schemaField": "schema_field",
        "unknown": "unknown",
    }
    depths = {verdict.model_urn: 0}
    queue = [verdict.model_urn]
    while queue:
        source = queue.pop(0)
        for target in graph.adjacency.get(source, []):
            if target not in depths:
                depths[target] = depths[source] + 1
                queue.append(target)
    evidence_nodes = {
        node for path in verdict.evidence_paths for node in path.path
    }
    rows: dict[int, int] = {}
    nodes = []
    for urn, node in graph.nodes.items():
        depth = depths.get(urn, max(depths.values(), default=0) + 1)
        row = rows.get(depth, 0)
        rows[depth] = row + 1
        nodes.append({
            "id": urn,
            "label": node.name,
            "type": type_map.get(node.type, "unknown"),
            "urn": urn,
            "description": node.description,
            "tags": sorted(node.tags),
            "glossaryTerms": sorted(node.glossary_terms),
            "isLeakNode": urn in evidence_nodes,
            "x": 24 + (max(depths.values(), default=0) - depth) * 190,
            "y": 24 + row * 72,
        })
    return {
        "nodes": nodes,
        "edges": [
            {
                "from": edge.target_urn,
                "to": edge.source_urn,
                "isLeak": edge.source_urn in evidence_nodes and edge.target_urn in evidence_nodes,
                "isBroken": edge.target_urn.startswith("unknown:"),
            }
            for edge in graph.edges
        ],
    }


def format_verdict_response(
    request: EvaluateRequest, request_id: str, latency_ms: int, verdict_obj: VerdictInternal, graph: InternalGraph
) -> dict:
    """Transform internal VerdictInternal object into UI response payload."""
    if verdict_obj.reason_code == "TARGET_LEAKAGE":
        headline = "Blocked — trained on data it shouldn’t have seen."
        explanation = "Target leakage detected in the acquired DataHub provenance graph."
        write_back = [
            {"entity": "MLModel", "urn": request.model_urn, "aspect": "globalTags", "operation": "UPSERT", "status": "REQUESTED"},
            {"entity": "Dataset", "urn": getattr(verdict_obj.evidence_paths[0], "tainted_urn", "unknown") if verdict_obj.evidence_paths else "unknown", "aspect": "incidents", "operation": "CREATE", "status": "REQUESTED"}
        ]
    elif verdict_obj.reason_code == "INCOMPLETE_LINEAGE":
        headline = "Blocked — insufficient lineage to approve."
        explanation = "The acquired DataHub provenance graph is incomplete; approval is denied."
        write_back = [
            {"entity": "MLModel", "urn": request.model_urn, "aspect": "globalTags", "operation": "UPSERT", "status": "REQUESTED"},
            {"entity": "MLModel", "urn": request.model_urn, "aspect": "incidents", "operation": "CREATE", "status": "REQUESTED"}
        ]
    elif verdict_obj.verdict == Verdict.APPROVED:
        headline = "Approved — full lineage resolved. No policy flags."
        explanation = "All configured policies completed without a match on the acquired DataHub provenance graph."
        write_back = {"status": "REQUESTED"}
    else:
        headline = "Blocked — a configured policy was violated."
        explanation = "A configured DataHub governance policy matched the acquired provenance graph."
        write_back = {"status": "REQUESTED"}

    evidence_paths_serialized = [
        (
            {
                "id": f"ev-{(i+1):02d}",
                "feature_urn": ep.feature_urn,
                "tainted_urn": ep.tainted_urn,
                "tag_found": ep.tag_found,
                "path": ep.path,
                "policy_id": ep.policy_id,
                "field_name": ep.field_name,
                "verdict": ep.verdict,
                "transform": ep.transform,
                "confidence": ep.confidence,
                "aspectPath": ep.aspect_path,
                "rationale": ep.rationale,
            }
            if hasattr(ep, "feature_urn")
            else ep
        )
        for i, ep in enumerate(verdict_obj.evidence_paths)
    ]

    execution_events_serialized = [
        (
            {
                "stage": ev.stage,
                "step_num": ev.step_num,
                "detail": ev.detail,
                "timestamp": ev.timestamp,
            }
            if hasattr(ev, "stage")
            else ev
        )
        for ev in getattr(verdict_obj, "execution_events", [])
    ]

    return {
        "request": {
            "model_urn": request.model_urn,
            "environment": request.environment,
            "action": request.action,
            "requested_by": request.requested_by,
            "request_id": request_id,
            "gms_endpoint": settings.gms_url,
        },
        "evaluation": {
            "verdict": verdict_obj.verdict,
            "reason_code": verdict_obj.reason_code,
            "headline": headline,
            "explanation": explanation,
            "latency_ms": latency_ms,
            "policies_evaluated": verdict_obj.policies_evaluated,
            "denials": sum(1 for ep in verdict_obj.evidence_paths if getattr(ep, "verdict", None) == "BLOCKED"),
            "warnings": sum(1 for ep in verdict_obj.evidence_paths if getattr(ep, "verdict", None) == "WARN"),
            "allowances": sum(1 for ep in verdict_obj.evidence_paths if getattr(ep, "verdict", None) == "APPROVED"),
        },
        "graph": graph_to_ui_payload(graph, verdict_obj),
        "write_back": write_back,
        "evidence_paths": evidence_paths_serialized,
        "execution_events": execution_events_serialized,
        "evaluated_at": datetime.now(timezone.utc).isoformat(),
        "evaluation_source": "live_datahub",
        "remediation_available": verdict_obj.verdict == Verdict.BLOCKED and bool(evidence_paths_serialized),
    }


@app.post("/evaluate")
async def evaluate_model_route(
    request: EvaluateRequest, background_tasks: BackgroundTasks
):
    import uuid
    import time

    """Evaluate a model for deployment safety."""
    request_id = f"UW-REQ-{str(uuid.uuid4())[:8].upper()}"
    start_time = time.time()
    response_payload = None
    internal_verdict = None

    try:
        client = get_metadata_client()
        if not client:
            raise UnderwriteError("DataHub client unavailable or unhealthy")

        agent = Agent(client=client, settings=settings, policies=GLOBAL_POLICIES)
        internal_verdict = agent.evaluate_model(request.model_urn)
        graph = agent.last_graph
        if graph is None:
            raise UnderwriteError("Evaluation completed without a graph")
        latency_ms = int((time.time() - start_time) * 1000)
        response_payload = format_verdict_response(request, request_id, latency_ms, internal_verdict, graph)
    except (UnderwriteError, OSError, ValueError) as e:
        logger.warning("Live evaluation failed (%s) — returning fail-closed response", e)

    if not response_payload:
        response_payload = {
            "request": {
                "model_urn": request.model_urn,
                "environment": request.environment,
                "action": request.action,
                "requested_by": request.requested_by,
                "request_id": request_id,
                "gms_endpoint": settings.gms_url,
            },
            "evaluation": {
                "verdict": Verdict.BLOCKED,
                "reason_code": ReasonCode.EVALUATION_UNAVAILABLE,
                "headline": "Blocked — evaluation unavailable.",
                "explanation": f"Evaluation could not be completed for model: {request.model_urn}",
                "latency_ms": int((time.time() - start_time) * 1000),
                "policies_evaluated": 0,
                "denials": 0,
                "warnings": 0,
                "allowances": 0,
            },
            "graph": None,
            "write_back": None,
            "evidence_paths": [],
            "execution_events": [],
            "evaluated_at": datetime.now(timezone.utc).isoformat(),
            "evaluation_source": "unavailable",
            "remediation_available": False,
        }

    if response_payload["evaluation_source"] == "live_datahub":
        background_tasks.add_task(
            process_verdict_writeback_event, response_payload, settings.gms_url
        )
        
    if response_payload["evaluation"]["verdict"] == Verdict.BLOCKED:
        policy_id = "UNKNOWN"
        if internal_verdict and internal_verdict.evidence_paths:
            policy_id = getattr(internal_verdict.evidence_paths[0], "policy_id", "UNKNOWN")
        context = RemediationContext(
            decision_id=request_id,
            model_urn=request.model_urn,
            policy_id=policy_id,
            reason_code=response_payload["evaluation"]["reason_code"],
            evidence_paths=tuple(internal_verdict.evidence_paths) if internal_verdict else ()
        )
        decision_store.put(request_id, context)
        
    return response_payload


@app.post("/remediation/{decision_id}")
async def remediation_route(decision_id: str):
    """Generate an AI remediation plan for a blocked deployment using DataHub context."""
    context = decision_store.get(decision_id)
    if not context:
        raise HTTPException(status_code=404, detail="Decision not found or evidence expired")
    
    remediation = generate(context)
    
    markdown = f"{DISCLAIMER}\n\n**{remediation.summary}**\n\n"
    for action in remediation.suggested_actions:
        markdown += f"{action}\n\n"
        
    return {"markdown": markdown.strip(), "source": remediation.source}


@app.post("/override")
async def override_verdict(
    request: OverrideRequest,
    background_tasks: BackgroundTasks,
    x_underwrite_override_token: str | None = Header(default=None),
):
    """Record a named override statement for the supplied model URN."""
    if not settings.override_token:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Overrides are disabled until UNDERWRITE_OVERRIDE_TOKEN is configured.",
        )
    if x_underwrite_override_token != settings.override_token:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="A valid X-Underwrite-Override-Token is required.",
        )
    timestamp = datetime.now(timezone.utc).isoformat()
    logger.info(
        "OVERRIDE: model=%s signer=%s at=%s",
        request.model_urn,
        request.signer_name,
        timestamp,
    )

    wb_client = DataHubWriteBackClient(settings.gms_url)
    background_tasks.add_task(
        wb_client.write_documentation,
        request.model_urn,
        f"OVERRIDDEN by {request.signer_name} at {timestamp}",
    )

    return {
        "status": "overridden",
        "signer_name": request.signer_name,
        "logged_at": timestamp,
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    client = get_metadata_client()
    if client:
        return {"status": "online", "datahub_gms": "connected", "mode": "live"}
    return {"status": "online", "datahub_gms": "offline", "mode": "cached_fallback"}


@app.get("/")
async def serve_index():
    """Serve main UI page."""
    return FileResponse(STATIC_DIR / "index.html")


app.mount("/assets", StaticFiles(directory="web/static/assets"), name="assets")
app.mount("/static", StaticFiles(directory="web/frontend"), name="static")


def main():
    """Main application launcher."""
    import uvicorn

    uvicorn.run("app:app", host=settings.host, port=settings.port, reload=True)


if __name__ == "__main__":
    main()

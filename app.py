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

from fastapi import BackgroundTasks, FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field, field_validator

from agent import Agent, InternalGraph, VerdictInternal
from config import settings
from datahub_client import DataHubWriteBackClient, process_verdict_writeback_event
from exceptions import UnderwriteError
from metadata.client import DataHubClient

logger = logging.getLogger("underwrite.server")

app = FastAPI(
    title="Underwrite",
    description="The signature a model needs before it's allowed to exist in production.",
)

BASE_DIR = Path(__file__).parent
STATIC_DIR = BASE_DIR / "static"
CACHE_DIR = BASE_DIR / "cache"


def get_metadata_client() -> DataHubClient | None:
    """Instantiate and test DataHubClient connection."""
    try:
        client = DataHubClient(settings.gms_url)
        return client if client.is_healthy() else None
    except (UnderwriteError, OSError, Exception) as e:
        logger.warning(
            "DataHub GMS connection test failed (%s) — running in cached mode", e
        )
        return None


def load_cached_verdicts() -> dict:
    """Load cached fallback verdicts."""
    verdicts_path = CACHE_DIR / "verdicts.json"
    if not verdicts_path.exists():
        logger.warning("cache/verdicts.json not found — fallback responses unavailable")
        return {}
    try:
        with open(verdicts_path) as f:
            data = json.load(f)
        if not isinstance(data, dict):
            raise ValueError("cache root must be an object")
        return data
    except (OSError, ValueError, json.JSONDecodeError) as e:
        logger.error("Ignoring invalid cached verdicts: %s", e)
        return {}


CACHED_VERDICTS = load_cached_verdicts()


class EvaluateRequest(BaseModel):
    model_urn: str = Field(..., description="Canonical DataHub ML Model URN")

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
            "tags": sorted(node.tags),
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
    model_urn: str, verdict_obj: VerdictInternal, graph: InternalGraph
) -> dict:
    """Transform internal VerdictInternal object into UI response payload."""
    if verdict_obj.reason_code == "TARGET_LEAKAGE":
        headline = "Blocked — trained on data it shouldn’t have seen."
        explanation = "Target leakage detected in the acquired DataHub provenance graph."
        write_back = {
            "tag": "model-at-risk",
            "incident": True,
            "text": "Write-back requested: model-at-risk tag and source-dataset incident.",
        }
    elif verdict_obj.reason_code == "INCOMPLETE_LINEAGE":
        headline = "Blocked — insufficient lineage to approve."
        explanation = "The acquired DataHub provenance graph is incomplete; approval is denied."
        write_back = {
            "tag": "model-at-risk",
            "incident": True,
            "text": "Write-back requested: model-at-risk tag and incomplete-lineage incident.",
        }
    elif verdict_obj.verdict == "approved":
        headline = "Approved — full lineage resolved. No policy flags."
        explanation = "All configured policies completed without a match on the acquired DataHub provenance graph."
        write_back = {
            "tag": "model-approved",
            "incident": False,
            "text": "Write-back requested: model-approved tag and verdict documentation.",
        }
    else:
        headline = "Blocked — a configured policy was violated."
        explanation = "A configured DataHub governance policy matched the acquired provenance graph."
        write_back = {
            "tag": "model-at-risk",
            "incident": True,
            "text": "Write-back requested: model-at-risk tag and source-dataset incident.",
        }

    evidence_paths_serialized = [
        (
            {
                "feature_urn": ep.feature_urn,
                "tainted_urn": ep.tainted_urn,
                "tag_found": ep.tag_found,
                "path": ep.path,
                "policy_id": ep.policy_id,
            }
            if hasattr(ep, "feature_urn")
            else ep
        )
        for ep in verdict_obj.evidence_paths
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
        "model_urn": model_urn,
        "verdict": verdict_obj.verdict,
        "reason_code": verdict_obj.reason_code,
        "headline": headline,
        "explanation": explanation,
        "graph": graph_to_ui_payload(graph, verdict_obj),
        "write_back": write_back,
        "evidence_paths": evidence_paths_serialized,
        "execution_events": execution_events_serialized,
        "evaluated_at": datetime.now(timezone.utc).isoformat(),
        "evaluation_source": "live_datahub",
    }


@app.post("/evaluate")
async def evaluate_model_route(
    request: EvaluateRequest, background_tasks: BackgroundTasks
):
    """Evaluate a model for deployment safety."""
    model_urn = request.model_urn
    response_payload = None

    try:
        client = get_metadata_client()
        if client:
            agent = Agent(client=client, settings=settings)
            internal_verdict = agent.evaluate_model(model_urn)
            graph = agent.last_graph
            if graph is None:
                raise UnderwriteError("Evaluation completed without a graph")
            response_payload = format_verdict_response(model_urn, internal_verdict, graph)
    except (UnderwriteError, OSError, ValueError) as e:
        logger.warning(
            "Live evaluation failed (%s) — returning cached verdict fallback", e
        )

    if not response_payload:
        cached = CACHED_VERDICTS.get(model_urn)
        if cached:
            response_payload = dict(cached)
            response_payload["model_urn"] = model_urn
            response_payload["evaluated_at"] = datetime.now(timezone.utc).isoformat()
            response_payload["evaluation_source"] = "cached_fixture"
            # Fixtures contain illustrative write-back fields, not evidence that
            # this request emitted metadata to a live GMS instance.
            response_payload["write_back"] = None
        else:
            response_payload = {
                "model_urn": model_urn,
                "verdict": "blocked",
                "reason_code": "EVALUATION_FAILED",
                "headline": "Blocked — evaluation unavailable.",
                "explanation": f"No evaluation data available for model: {model_urn}",
                "graph": None,
                "write_back": None,
                "evaluated_at": datetime.now(timezone.utc).isoformat(),
                "evaluation_source": "unavailable",
            }

    background_tasks.add_task(
        process_verdict_writeback_event, response_payload, settings.gms_url
    )
    return response_payload


@app.post("/override")
async def override_verdict(request: OverrideRequest, background_tasks: BackgroundTasks):
    """Record a named override statement for the supplied model URN."""
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


if STATIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")


def main():
    """Main application launcher."""
    import uvicorn

    uvicorn.run("app:app", host=settings.host, port=settings.port, reload=True)


if __name__ == "__main__":
    main()

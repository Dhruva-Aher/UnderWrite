"""Underwrite — Guided Remediation Advisor (remediation.py)

This module implements the downstream Remediation Advisor.
PRINCIPLES:
1. The deterministic engine is the only authority.
2. The AI NEVER influences deployment decisions.
3. The AI only receives immutable evidence from the deterministic engine.
4. The AI cannot override, modify, or reinterpret the verdict.
5. The AI exists solely to reduce developer recovery time.
"""

import logging
from pydantic import BaseModel, Field

from config import settings
from llm_provider import get_llm

logger = logging.getLogger("underwrite.remediation")

class RemediationRequest(BaseModel):
    model_urn: str
    evidence_path: dict
    policy_id: str
    
class RemediationResponse(BaseModel):
    disclaimer_banner: str = Field(description="Must exactly match the provided DISCLAIMER constant.")
    root_cause: str = Field(description="Detailed explanation of why the data reached the model and violated the policy.")
    evidence_summary: str = Field(description="Summary of the lineage hops, schema fields, and evidence quality.")
    files_to_inspect: list[str] = Field(description="List of specific files, models, or dataset URNs to inspect in the codebase.")
    suggested_investigation: str = Field(description="Actionable advice on what to look for and how to resolve the leakage.")
    potential_patch: str = Field(description="A Markdown code block showing a potential SQL, YAML, or Python patch. Say 'Information not available in DataHub' if you cannot determine a patch.")
    pr_comment: str = Field(description="A concise summary suitable for posting as a GitHub PR comment.")
    slack_summary: str = Field(description="A short, alert-style summary suitable for a Slack notification.")
    blast_radius: list[str] = Field(description="List of downstream datasets, dashboards, or models affected by this incident.")
    datahub_owner_github: str = Field(description="The GitHub handle of the DataHub owner of the affected model or dataset, if available.")

DISCLAIMER = (
    "================================================\n\n"
    "REMEDIATION ADVISOR\n\n"
    "This recommendation DID NOT participate in the deployment decision.\n\n"
    "The deployment was already blocked by the deterministic runtime.\n\n"
    "================================================"
)

def _generate_fallback(request: RemediationRequest) -> RemediationResponse:
    ep = request.evidence_path
    feature_urn = ep.get("feature_urn", "unknown")
    tainted_urn = ep.get("tainted_urn", "unknown")
    tag = ep.get("tag_found", "unknown")
    field_name = ep.get("field_name", "unknown")
    path = ep.get("path", [])
    
    dataset_name = tainted_urn.split(",")[-1].replace(")", "") if "," in tainted_urn else tainted_urn
    feature_name = feature_urn.split(",")[-1].replace(")", "") if "," in feature_urn else feature_urn
    if field_name == "unknown":
        field_name = tainted_urn.split(",")[-1].replace(")", "") if "," in tainted_urn else "unknown_column"
    
    root_cause = f"The feature `{feature_name}` inherits from `{dataset_name}.{field_name}`, which carries the restricted `{tag}` tag. This violates the `{request.policy_id}` deterministic policy."
    
    lineage_hops = len(path) - 1 if path else 0
    schema_fields = sum(1 for node in path if "schemaField" in node)
    
    evidence_summary = (
        f"{lineage_hops} lineage hops\n"
        f"{schema_fields} schema fields\n"
        f"Evidence Quality\n\nHIGH (Deterministic Fallback)"
    )
    
    files_to_inspect = [f"models/staging/{dataset_name}.sql"]
    suggested_investigation = f"Consider examining the `{dataset_name}` transformation model to determine if the `{field_name}` column can be safely removed before aggregation into the feature store."
    patch = f"```sql\n-- Potential change: models/staging/{dataset_name}.sql\nSELECT\n    user_id,\n    -- {field_name},\n    created_at\nFROM {{{{ source('raw', '{dataset_name}') }}}}\n```"
    
    pr_comment = f"⚠️ Deployment blocked due to {request.policy_id} on {dataset_name}.{field_name}."
    slack_summary = f":warning: Deployment blocked for {request.model_urn}. Issue: {tag} tag on {field_name}."
    blast_radius = [request.model_urn]
    owner_github = "unknown_owner"

    logger.info("Generated FALLBACK AI remediation for model: %s", request.model_urn)
    return RemediationResponse(
        disclaimer_banner=DISCLAIMER,
        root_cause=root_cause,
        evidence_summary=evidence_summary,
        files_to_inspect=files_to_inspect,
        suggested_investigation=suggested_investigation,
        potential_patch=patch,
        pr_comment=pr_comment,
        slack_summary=slack_summary,
        blast_radius=blast_radius,
        datahub_owner_github=owner_github
    )

def _build_datahub_tools(gms_url: str) -> list:
    """Build DataHub Agent Context Kit LangChain tools using the real published API.

    The official package is ``datahub-agent-context`` (PyPI).  The public
    entrypoint is ``datahub_agent_context.langchain_tools.build_langchain_tools``
    which accepts a ``DataHubClient`` instance and returns a list of LangChain
    ``BaseTool`` objects (search, get_entity, get_lineage, etc.).

    We set ``include_mutations=False`` so the Remediation Advisor is read-only
    and structurally incapable of mutating the graph.
    """
    from datahub.sdk.main_client import DataHubClient
    from datahub_agent_context.langchain_tools import build_langchain_tools

    client = DataHubClient(server=gms_url)
    return build_langchain_tools(client, include_mutations=False)


def generate_hypothesis(request: RemediationRequest) -> RemediationResponse:
    """
    Generates a remediation plan using the deterministic evidence.
    This acts as a strict advisor that operates only on immutable deterministic evidence.
    Attempts to use DataHub Agent Context Kit + LLM. Falls back on failure.
    """
    llm = get_llm()
    if not llm:
        logger.warning("No LLM configured or missing keys. Falling back to deterministic template.")
        return _generate_fallback(request)

    try:
        from langchain.agents import AgentExecutor, create_tool_calling_agent
        from langchain_core.prompts import ChatPromptTemplate
    except ImportError as e:
        logger.warning("LangChain not installed: %s. Falling back.", e)
        return _generate_fallback(request)

    try:
        tools = _build_datahub_tools(settings.gms_url)
    except Exception as e:
        logger.warning("Agent Context Kit unavailable (%s). Falling back.", e)
        return _generate_fallback(request)

    try:
        prompt = ChatPromptTemplate.from_messages([
            ("system",
             "You are the Underwrite Remediation Advisor.\n"
             "The deployment was ALREADY blocked by a deterministic engine.\n"
             "You CANNOT change the verdict.\n"
             "Your job is to use DataHub tools (search, get_entity, get_lineage) "
             "to investigate the tainted URN and its lineage, "
             "calculate the blast radius (downstream affected assets), "
             "find the DataHub owner's GitHub handle, "
             "and recommend exactly how the developer can fix it.\n\n"
             "Rules:\n"
             "1. ONLY use information obtained from DataHub tools or the provided evidence.\n"
             "2. If you cannot find info in DataHub, explicitly say 'Information not available in DataHub'.\n"
             "3. Output must be structured strictly to match the requested JSON format.\n"
             "4. Do NOT fabricate metadata, lineage, ownership, or schemas."
            ),
            ("human",
             "Model URN: {model_urn}\n"
             "Policy Violated: {policy_id}\n"
             "Evidence Path: {evidence_path}\n\n"
             "Please investigate this using your DataHub tools. Find the upstream dataset/schema, "
             "check its tags, description, and owners to identify the GitHub handle of the owner. "
             "Also query the lineage to determine all downstream assets affected (blast radius). "
             "Then generate the remediation advice."
            ),
            ("placeholder", "{agent_scratchpad}")
        ])

        agent = create_tool_calling_agent(llm, tools, prompt)
        agent_executor = AgentExecutor(
            agent=agent, tools=tools, verbose=True,
            handle_parsing_errors=True, max_iterations=6,
        )

        logger.info("Invoking AI Agent with DataHub Agent Context Kit for model: %s", request.model_urn)

        raw_result = agent_executor.invoke({
            "model_urn": request.model_urn,
            "policy_id": request.policy_id,
            "evidence_path": str(request.evidence_path),
        })

        investigation_summary = raw_result["output"]

        parser_prompt = ChatPromptTemplate.from_messages([
            ("system",
             "Extract the following information from the investigation summary "
             "into the provided schema. Do not fabricate anything. If missing, "
             "indicate it's not available in DataHub."),
            ("human",
             "Investigation Summary:\n{summary}\n\nEvidence Bundle:\n{evidence}")
        ])

        structured_llm = llm.with_structured_output(RemediationResponse)
        formatting_chain = parser_prompt | structured_llm

        structured_response = formatting_chain.invoke({
            "summary": investigation_summary,
            "evidence": str(request.evidence_path),
        })

        # Overwrite disclaimer — the LLM is not allowed to change this.
        structured_response.disclaimer_banner = DISCLAIMER

        logger.info("AI Remediation completed via Agent Context Kit for model: %s", request.model_urn)
        return structured_response

    except Exception as e:
        logger.error("AI Remediation failed: %s. Falling back to deterministic template.", e, exc_info=True)
        return _generate_fallback(request)


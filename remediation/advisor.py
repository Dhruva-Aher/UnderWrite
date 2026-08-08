"""Underwrite — Guided Remediation Advisor (remediation/advisor.py)"""
import logging
from pydantic import BaseModel
from llm_provider import get_llm
from config import settings
from langgraph.prebuilt import create_react_agent
try:
    from datahub_agent_context.langchain_tools import build_langchain_tools
except ImportError:
    build_langchain_tools = None

logger = logging.getLogger("underwrite.remediation")

DISCLAIMER = (
    "================================================\n\n"
    "REMEDIATION ADVISOR\n\n"
    "This recommendation DID NOT participate in the deployment decision.\n\n"
    "The deployment was already blocked by the deterministic runtime.\n\n"
    "================================================\n"
)

from dataclasses import dataclass
from typing import Literal
from agent import EvidencePath
from constants import ReasonCode

@dataclass(frozen=True)
class RemediationContext:
    decision_id: str
    model_urn: str
    policy_id: str
    reason_code: ReasonCode
    evidence_paths: tuple[EvidencePath, ...]

@dataclass(frozen=True)
class Remediation:
    summary: str
    suggested_actions: tuple[str, ...]
    source: Literal["ack_llm", "deterministic"]

def deterministic_fallback(context: RemediationContext) -> Remediation:
    evidence_md = ""
    for idx, ep in enumerate(context.evidence_paths):
        evidence_md += f"**Evidence {idx + 1}**\n"
        evidence_md += f"- Path: {' -> '.join(ep.path)}\n"
        if hasattr(ep, "field_name"):
            evidence_md += f"- Field: {ep.field_name}\n"
    
    return Remediation(
        summary=f"Deployment for {context.model_urn} blocked by {context.policy_id}.",
        suggested_actions=("Review the evidence paths provided.", "Remove the upstream dependencies violating the policy.", f"Evidence:\n{evidence_md}"),
        source="deterministic"
    )

def generate(context: RemediationContext) -> Remediation:
    """
    Format evidence to markdown -> send to LLM (with DataHub ACK tools).

    ACK requires the official ``datahub.sdk`` DataHubClient, not Underwrite's
    metadata wrapper used by the deterministic gate.
    """
    try:
        if not build_langchain_tools:
            raise ValueError("datahub_agent_context.langchain_tools unavailable")
        from datahub.sdk.main_client import DataHubClient as SdkDataHubClient

        sdk_client = SdkDataHubClient(
            server=settings.gms_url,
            token=settings.datahub_token,
        )
        tools = build_langchain_tools(sdk_client, include_mutations=False)
        if not tools:
            raise ValueError("build_langchain_tools returned empty or None")
    except Exception as e:
        logger.warning("DataHub ACK unavailable (%s); returning deterministic evidence-only remediation", e)
        return deterministic_fallback(context)
        
    evidence_md = ""
    for idx, ep in enumerate(context.evidence_paths):
        evidence_md += f"**Evidence {idx + 1}**\n"
        evidence_md += f"- Path: {' -> '.join(ep.path)}\n"
        if hasattr(ep, "field_name"):
            evidence_md += f"- Field: {ep.field_name}\n"
    
    prompt = f"""You are a Remediation Advisor.
A deployment for model {context.model_urn} was blocked due to a violation of policy {context.policy_id}.

Here is the deterministic evidence of the violation:
{evidence_md}

Investigate the upstream entities involved using your tools and provide actionable advice to the developer on how to fix this issue.
"""

    llm = get_llm()
    if not llm:
        logger.warning("No LLM configured. Returning deterministic fallback.")
        return deterministic_fallback(context)

    try:
        agent_executor = create_react_agent(llm, tools)
        result = agent_executor.invoke({"messages": [("user", prompt)]})
        content = result["messages"][-1].content
        return Remediation(
            summary=f"Analysis for {context.model_urn}",
            suggested_actions=(content,),
            source="ack_llm"
        )
    except Exception as e:
        logger.error("LLM generation failed: %s", e)
        return deterministic_fallback(context)

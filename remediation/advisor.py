"""Underwrite — Guided Remediation Advisor (remediation/advisor.py)"""
import logging
from pydantic import BaseModel
from llm_provider import get_llm
from config import settings
from datahub_client import create_datahub_client
from langchain.agents import initialize_agent, AgentType

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

class RemediationRequest(BaseModel):
    model_urn: str
    evidence_paths: list[dict]
    policy_id: str

def generate(request: RemediationRequest) -> str:
    """
    Format evidence to markdown -> send to LLM (with DataHub ACK tools) -> return markdown.
    """
    evidence_md = ""
    for idx, ep in enumerate(request.evidence_paths):
        evidence_md += f"**Evidence {idx + 1}**\n"
        for k, v in ep.items():
            evidence_md += f"- {k}: {v}\n"
        evidence_md += "\n"
    
    prompt = f"""You are a Remediation Advisor.
A deployment for model {request.model_urn} was blocked due to a violation of policy {request.policy_id}.

Here is the deterministic evidence of the violation:
{evidence_md}

Investigate the upstream entities involved using your tools and provide actionable advice to the developer on how to fix this issue.
Format your response in Markdown. Do not include a disclaimer banner, it will be added automatically.
"""

    llm = get_llm()
    if not llm:
        logger.warning("No LLM configured. Returning basic markdown.")
        return f"{DISCLAIMER}\n\n**Action Required:**\nDeployment for {request.model_urn} blocked by {request.policy_id}.\n\n**Evidence:**\n```\n{evidence_md}\n```\n"

    try:
        client = create_datahub_client(settings)
        tools = []
        if build_langchain_tools:
            tools = build_langchain_tools(client, include_mutations=False)
        
        if tools:
            agent = initialize_agent(
                tools, llm, agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION, verbose=False
            )
            content = agent.run(prompt)
        else:
            response = llm.invoke(prompt)
            content = response.content if hasattr(response, "content") else str(response)
            
        return f"{DISCLAIMER}\n\n{content}"
    except Exception as e:
        logger.error("LLM generation failed: %s", e)
        return f"{DISCLAIMER}\n\n**Action Required:**\nDeployment for {request.model_urn} blocked by {request.policy_id}.\n\n**Evidence:**\n```\n{evidence_md}\n```\n"

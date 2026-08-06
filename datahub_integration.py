"""Underwrite — DataHub Integration Layer (datahub_integration.py)

Converts an InvestigationReport into a DataHub Incident payload.
This layer only consumes the report; it does no investigation or verification.
"""

import logging
from typing import Protocol, Any
from remediation_engine import InvestigationReport

logger = logging.getLogger("underwrite.datahub")


from metadata.client import DataHubClient, MetadataClient

class DataHubRenderer:
    """Renders an InvestigationReport to DataHub."""
    
    def __init__(self, client: MetadataClient):
        self.client = client
        self.formatter = DataHubFormatter()

    def render_to_datahub(self, report: InvestigationReport, target_urn: str, pr_url: str = "") -> str:
        """
        Creates a DataHub Incident and links it to a PR.
        """
        payload = self.formatter.format_incident_payload(report, pr_url)
        
        # In metadata.client, write_incident signature is (dataset_urn, model_urn, incident_type, description)
        # We will use the target_urn as both for the incident attachment, and "Underwrite Remediation" as type.
        self.client.write_incident(
            dataset_urn=target_urn,
            model_urn=target_urn,
            incident_type="AI_REMEDIATION",
            description=payload["description"]
        )
        
        incident_id = f"incident-{report.investigation_id}"
        
        # Additionally, emit a documentation aspect with the PR link
        if pr_url:
            doc_text = f"Remediated via AI. Pull Request: {pr_url}"
            self.client.write_documentation(target_urn, doc_text)
            
        logger.info("Successfully rendered InvestigationReport %s to DataHub Incident", report.investigation_id)
        return incident_id


class DataHubFormatter:
    """Formats an InvestigationReport into a rich DataHub Incident payload."""
    
    @staticmethod
    def format_incident_payload(report: InvestigationReport, pr_url: str = "") -> dict[str, Any]:
        initial_evidence = report.attempts[0].evidence_count_before if report.attempts else len(report.evidence)
        remaining_evidence = report.attempts[-1].evidence_count_after if report.attempts else len(report.evidence)
        
        description = (
            f"**Status:** Draft Remediation Ready\n\n"
            f"**Policy:** {report.policy}\n\n"
            f"**Root Cause:**\n{report.root_cause}\n\n"
            f"**Blast Radius:**\n"
            f"- Datasets: {report.blast_radius.datasets}\n"
            f"- Models: {report.blast_radius.models}\n"
            f"- Dashboards: {report.blast_radius.dashboards}\n\n"
            f"**Owner:** @{report.blast_radius.owner}\n\n"
            f"**Verification:** {report.status}\n\n"
            f"**Confidence:** {report.confidence}%\n\n"
            f"**Evidence Summary:**\n"
            f"{initial_evidence} leakage paths detected.\n"
            f"After deterministic remediation:\n"
            f"{remaining_evidence} remain.\n"
            f"Verified successfully.\n\n"
        )
        
        if pr_url:
            description += f"**Pull Request:** {pr_url}\n\n"
            
        description += f"**Investigation ID:** `{report.investigation_id}`\n"
        
        return {
            "title": f"[AI Remediation] {report.policy} resolved",
            "description": description,
            "type": "CUSTOM",
            "customType": "Data Reliability Violation",
            "priority": "HIGH",
            "status": "ACTIVE" if not report.ready_for_pr else "RESOLVED"
        }




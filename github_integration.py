"""Underwrite — GitHub Integration Layer (github_integration.py)

Converts an InvestigationReport into a production-quality GitHub Pull Request.
This layer only consumes the report; it does no investigation or verification.
"""

import logging
from typing import Protocol
from remediation_engine import InvestigationReport

logger = logging.getLogger("underwrite.github")

class MarkdownFormatter:
    """Formats an InvestigationReport into a Staff Engineer quality PR body."""
    
    @staticmethod
    def format_pr_body(report: InvestigationReport) -> str:
        lines = []
        lines.append("## 🟢 Deterministically Verified")
        lines.append("")
        lines.append(f"**Policy:** {report.policy}")
        lines.append(f"**Status:** {report.status}")
        lines.append("")
        lines.append("---")
        lines.append("## Summary")
        lines.append("")
        lines.append(f"{report.policy.replace('_', ' ').title()} detected and remediated.")
        lines.append("")
        lines.append("## Root Cause")
        lines.append("")
        lines.append(report.root_cause)
        lines.append("")
        lines.append("## Blast Radius")
        lines.append("")
        lines.append(f"- **Datasets:** {report.blast_radius.datasets}")
        lines.append(f"- **Models:** {report.blast_radius.models}")
        lines.append(f"- **Dashboards:** {report.blast_radius.dashboards}")
        lines.append("")
        lines.append("## Investigation")
        lines.append("")
        lines.append("> **LLMs propose. Deterministic systems decide.**")
        lines.append("")
        lines.append(f"Investigation ID: `{report.investigation_id}`")
        lines.append("")
        lines.append("## Proposed Patch")
        lines.append("")
        if report.final_patch:
            lines.append(f"**File:** `{report.final_patch.file_path}`")
            lines.append("```diff")
            lines.append(f"- {report.final_patch.search_text}")
            lines.append(f"+ {report.final_patch.replace_text}")
            lines.append("```")
        else:
            lines.append("No patch generated.")
        lines.append("")
        lines.append("## Deterministic Verification")
        lines.append("")
        lines.append(report.status)
        lines.append("")
        lines.append("Evidence Paths")
        if report.attempts:
            path_str = f"{report.attempts[0].evidence_count_before}"
            for attempt in report.attempts:
                path_str += f" → {attempt.evidence_count_after}"
            lines.append(path_str)
        else:
            lines.append(str(len(report.evidence)))
        lines.append("")
        lines.append("## Confidence")
        lines.append("")
        lines.append(f"{report.confidence}%")
        lines.append("")
        lines.append("## DataHub")
        lines.append("")
        lines.append(f"- **Incident:** `Pending`")
        lines.append(f"- **Owner:** `@{report.blast_radius.owner}`")
        return "\n".join(lines)


class GitHubClient(Protocol):
    """Protocol for interacting with GitHub (PyGithub or requests wrapper)."""
    def create_pull_request(self, title: str, body: str, branch: str) -> str: ...
    def add_labels(self, pr_id: str, labels: list[str]) -> None: ...
    def assign_reviewer(self, pr_id: str, reviewer: str) -> None: ...


class MockGitHubClient:
    """Mock client for deterministic dry-runs and demos."""
    def create_pull_request(self, title: str, body: str, branch: str) -> str:
        logger.info("Creating PR on branch '%s': %s", branch, title)
        return "PR-123"
        
    def add_labels(self, pr_id: str, labels: list[str]) -> None:
        logger.info("Added labels %s to %s", labels, pr_id)
        
    def assign_reviewer(self, pr_id: str, reviewer: str) -> None:
        logger.info("Assigned reviewer @%s to %s", reviewer, pr_id)


class GitHubRenderer:
    """Renders an InvestigationReport to GitHub."""
    def __init__(self, client: GitHubClient):
        self.client = client
        self.formatter = MarkdownFormatter()

    def render_to_github(self, report: InvestigationReport, branch_name: str) -> str:
        """
        Creates a PR, adds deterministic labels, and assigns the DataHub owner.
        """
        if not report.ready_for_pr:
            logger.warning("Report %s is not ready for PR. Aborting.", report.investigation_id)
            return ""

        title = f"fix(data): Remediate {report.policy} violation [{report.investigation_id}]"
        body = self.formatter.format_pr_body(report)
        
        pr_id = self.client.create_pull_request(title, body, branch_name)
        
        # Determine labels based on report
        labels = ["datahub", "ai-remediation", "verified", report.policy.lower().replace("_", "-")]
        self.client.add_labels(pr_id, labels)
        
        # Assign reviewer directly from blast radius metadata
        owner = report.blast_radius.owner
        if owner and owner.lower() != "unknown":
            self.client.assign_reviewer(pr_id, owner)
            
        logger.info("Successfully rendered InvestigationReport %s to GitHub PR %s", report.investigation_id, pr_id)
        return pr_id

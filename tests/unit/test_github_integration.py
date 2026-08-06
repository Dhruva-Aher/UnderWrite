import pytest
from unittest.mock import MagicMock
from remediation_engine import InvestigationReport, BlastRadiusInfo, PatchAttempt, ProposedPatch
from github_integration import MarkdownFormatter, GitHubRenderer, MockGitHubClient

def test_markdown_formatter():
    report = InvestigationReport(
        investigation_id="INV-999",
        policy="TARGET_LEAKAGE",
        status="APPROVED",
        root_cause="Test leak",
        evidence=[],
        blast_radius=BlastRadiusInfo(datasets=2, models=1, dashboards=0, owner="dhruv"),
        attempts=[
            PatchAttempt(
                attempt_number=1,
                patch=ProposedPatch(file_path="a.sql", search_text="old", replace_text="new", severed_urns=[], rationale=""),
                verification_passed=True,
                evidence_count_before=5,
                evidence_count_after=0,
                message="Done"
            )
        ],
        final_patch=ProposedPatch(file_path="a.sql", search_text="old", replace_text="new", severed_urns=[], rationale=""),
        confidence=99.0,
        verification_summary="Clean",
        ready_for_pr=True
    )
    
    body = MarkdownFormatter.format_pr_body(report)
    
    assert "## 🟢 Deterministically Verified" in body
    assert "**Policy:** TARGET_LEAKAGE" in body
    assert "LLMs propose. Deterministic systems decide." in body
    assert "5 → 0" in body
    assert "@dhruv" in body
    assert "```diff" in body
    assert "- old" in body
    assert "+ new" in body

def test_github_renderer_success():
    report = InvestigationReport(
        investigation_id="INV-999",
        policy="TARGET_LEAKAGE",
        status="APPROVED",
        root_cause="Test leak",
        evidence=[],
        blast_radius=BlastRadiusInfo(datasets=2, models=1, dashboards=0, owner="dhruv"),
        attempts=[],
        final_patch=None,
        confidence=99.0,
        verification_summary="Clean",
        ready_for_pr=True
    )
    
    mock_client = MagicMock()
    mock_client.create_pull_request.return_value = "PR-1"
    
    renderer = GitHubRenderer(mock_client)
    pr_id = renderer.render_to_github(report, "fix-branch")
    
    assert pr_id == "PR-1"
    mock_client.create_pull_request.assert_called_once()
    mock_client.add_labels.assert_called_once_with("PR-1", ["datahub", "ai-remediation", "verified", "target-leakage"])
    mock_client.assign_reviewer.assert_called_once_with("PR-1", "dhruv")

def test_github_renderer_aborts_if_not_ready():
    report = InvestigationReport(
        investigation_id="INV-999",
        policy="TARGET_LEAKAGE",
        status="BLOCKED",
        root_cause="Test leak",
        evidence=[],
        blast_radius=BlastRadiusInfo(datasets=2, models=1, dashboards=0, owner="unknown"),
        attempts=[],
        final_patch=None,
        confidence=0.0,
        verification_summary="Failed",
        ready_for_pr=False
    )
    
    mock_client = MagicMock()
    renderer = GitHubRenderer(mock_client)
    pr_id = renderer.render_to_github(report, "fix-branch")
    
    assert pr_id == ""
    mock_client.create_pull_request.assert_not_called()

import pytest
from unittest.mock import MagicMock
from remediation_engine import InvestigationReport, BlastRadiusInfo, PatchAttempt, ProposedPatch
from metadata.client import MockMetadataClient
from datahub_integration import DataHubFormatter, DataHubRenderer

def test_datahub_formatter():
    report = InvestigationReport(
        investigation_id="INV-007",
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
                evidence_count_before=7,
                evidence_count_after=0,
                message="Done"
            )
        ],
        final_patch=ProposedPatch(file_path="a.sql", search_text="old", replace_text="new", severed_urns=[], rationale=""),
        confidence=98.5,
        verification_summary="Clean",
        ready_for_pr=True
    )
    
    payload = DataHubFormatter.format_incident_payload(report, pr_url="https://github.com/pr/1")
    
    assert payload["type"] == "CUSTOM"
    assert payload["status"] == "RESOLVED"
    assert "7 leakage paths detected" in payload["description"]
    assert "0 remain" in payload["description"]
    assert "https://github.com/pr/1" in payload["description"]
    assert "INV-007" in payload["description"]

def test_datahub_renderer():
    report = InvestigationReport(
        investigation_id="INV-007",
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
    
    mock_client = MagicMock(spec=MockMetadataClient)
    
    renderer = DataHubRenderer(mock_client)
    incident_id = renderer.render_to_datahub(report, "urn:li:dataset:test", "http://pr")
    
    assert "incident-" in incident_id
    mock_client.write_incident.assert_called_once()
    mock_client.write_documentation.assert_called_once_with("urn:li:dataset:test", "Remediated via AI. Pull Request: http://pr")

import pytest
from remediation_engine import InvestigationReport, PatchAttempt, ProposedPatch, BlastRadiusInfo, EvidencePath
from ux import format_investigation_report

def test_format_investigation_report():
    ep = EvidencePath(
        feature_urn="urn:li:mlFeature:test",
        tainted_urn="urn:li:dataset:tainted",
        tag_found="urn:li:tag:post_outcome",
        path=["a", "b", "c"]
    )
    
    report = InvestigationReport(
        investigation_id="INV-TEST",
        policy="TARGET_LEAKAGE",
        status="APPROVED",
        root_cause="Some cause",
        evidence=[ep],
        blast_radius=BlastRadiusInfo(datasets=1, models=2, dashboards=3, owner="alice"),
        attempts=[
            PatchAttempt(
                attempt_number=1,
                patch=ProposedPatch(
                    file_path="model.sql",
                    search_text="SELECT *",
                    replace_text="SELECT a",
                    severed_urns=["urn:li:dataset:tainted"],
                    rationale="Fix"
                ),
                verification_passed=True,
                evidence_count_before=5,
                evidence_count_after=0,
                message="Target leakage path removed."
            )
        ],
        final_patch=None,
        confidence=98.0,
        verification_summary="Fixed",
        ready_for_pr=True
    )
    
    output = format_investigation_report(report)
    
    assert "UNDERWRITE AI DATA RELIABILITY ENGINE" in output
    assert "INV-TEST" in output
    assert "alice" in output
    assert "Before" in output
    assert "5" in output
    assert "↓" in output
    assert "0" in output
    assert "✓ TARGET_LEAKAGE" in output
    assert "Ready for GitHub PR" in output

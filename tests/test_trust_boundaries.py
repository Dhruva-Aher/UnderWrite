"""Tests for Underwrite Trust Boundaries."""
import pytest
from fastapi.testclient import TestClient
from app import app
from constants import Verdict, ReasonCode

client = TestClient(app)

def test_verdict_cannot_be_overridden_via_payload():
    # Even if an attacker tries to pass an approved verdict in the request,
    # the server should ignore it and evaluate based on DataHub metadata.
    
    payload = {
        "model_urn": "urn:li:mlModel:(urn:li:dataPlatform:mlflow,churn_model_v2,PROD)",
        "environment": "PROD",
        "action": "DEPLOY",
        "verdict": "approved", # Malicious attempt to override
        "reason_code": "CLEAN"
    }
    
    response = client.post("/evaluate", json=payload)
    assert response.status_code == 200
    
    data = response.json()
    # The evaluation should be UNAVAILABLE (since we aren't mocking DataHub for the TestClient)
    # or BLOCKED, but NEVER approved just because it was in the payload.
    assert data["evaluation"]["verdict"] == Verdict.BLOCKED
    assert data["evaluation"]["reason_code"] == ReasonCode.EVALUATION_UNAVAILABLE

def test_remediation_advisor_cannot_change_verdict():
    # Remediation is purely advisory and operates on static evidence.
    payload = {
        "model_urn": "urn:li:mlModel:(urn:li:dataPlatform:mlflow,model1,PROD)",
        "evidence_paths": [{"path": ["a", "b"]}],
        "policy_id": "GOV-12"
    }
    
    response = client.post("/remediation/dummy-id", json=payload)
    assert response.status_code == 200
    data = response.json()
    
    # Must contain the disclaimer banner enforcing the boundary
    assert "DID NOT participate in the deployment decision" in data["markdown"]

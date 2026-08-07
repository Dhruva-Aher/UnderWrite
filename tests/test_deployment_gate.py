import pytest
from unittest.mock import patch, MagicMock
import sys
from pathlib import Path
import httpx

# Add scripts directory to path to import deployment_gate
scripts_dir = Path(__file__).parent.parent / "scripts"
sys.path.append(str(scripts_dir))
import deployment_gate

@pytest.fixture
def mock_httpx_post():
    with patch("httpx.Client.post") as mock_post:
        yield mock_post

def setup_mock_response(mock_post, payload):
    mock_response = MagicMock()
    mock_response.json.return_value = payload
    mock_response.raise_for_status.return_value = None
    mock_post.return_value = mock_response

def run_gate_func(model_urn: str) -> int:
    return deployment_gate.evaluate_deployment("http://dummy", model_urn, 1.0)

def test_deployment_gate_approved_live(mock_httpx_post):
    setup_mock_response(mock_httpx_post, {
        "evaluation": {"verdict": "approved", "reason_code": "CLEAN"},
        "evaluation_source": "live_datahub"
    })
    assert run_gate_func("urn:li:mlModel:approved_live") == 0

def test_deployment_gate_blocked_target(mock_httpx_post):
    setup_mock_response(mock_httpx_post, {
        "evaluation": {"verdict": "blocked", "reason_code": "TARGET_LEAKAGE"},
        "evaluation_source": "live_datahub"
    })
    assert run_gate_func("urn:li:mlModel:blocked_target") == 1

def test_deployment_gate_blocked_incomplete(mock_httpx_post):
    setup_mock_response(mock_httpx_post, {
        "evaluation": {"verdict": "blocked", "reason_code": "INCOMPLETE_LINEAGE"},
        "evaluation_source": "live_datahub"
    })
    assert run_gate_func("urn:li:mlModel:blocked_incomplete") == 1

def test_deployment_gate_blocked_unavailable(mock_httpx_post):
    setup_mock_response(mock_httpx_post, {
        "evaluation": {"verdict": "blocked", "reason_code": "EVALUATION_UNAVAILABLE"},
        "evaluation_source": "unavailable"
    })
    assert run_gate_func("urn:li:mlModel:blocked_unavailable") == 1

def test_deployment_gate_approved_offline_fails(mock_httpx_post):
    setup_mock_response(mock_httpx_post, {
        "evaluation": {"verdict": "approved", "reason_code": "CLEAN"},
        "evaluation_source": "offline_fixture"
    })
    assert run_gate_func("urn:li:mlModel:approved_offline") == 1


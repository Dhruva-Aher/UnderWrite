"""Tests for the CI/CD deployment gate."""

from scripts.deployment_gate import evaluate_deployment


class Response:
    def __init__(self, payload):
        self.payload = payload

    def raise_for_status(self):
        return None

    def json(self):
        return self.payload


def test_gate_allows_only_live_approved_evaluations(monkeypatch):
    monkeypatch.setattr(
        "httpx.Client.post",
        lambda *args, **kwargs: Response(
            {"evaluation_source": "live_datahub", "evaluation": {"verdict": "approved"}}
        ),
    )

    result = evaluate_deployment("http://underwrite", "urn:test", 1)

    assert result == 0


def test_gate_blocks_cached_or_blocked_results(monkeypatch):
    monkeypatch.setattr(
        "httpx.Client.post",
        lambda *args, **kwargs: Response(
            {"evaluation_source": "cached_fixture", "verdict": "approved"}
        ),
    )

    result = evaluate_deployment("http://underwrite", "urn:test", 1)

    assert result == 1

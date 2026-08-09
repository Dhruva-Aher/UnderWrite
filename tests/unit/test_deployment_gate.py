"""Tests for the CI/CD deployment gate."""

from scripts.deployment_gate import (
    dataset_urn_from_schema_field,
    datahub_entity_url,
    default_principal,
    evaluate_deployment,
    process_payload,
)


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


def test_gate_sends_requesting_principal(monkeypatch):
    """A blank audit trail is worse than a wrong one; CI must identify itself."""
    sent = {}

    def capture(self, url, json=None, **kwargs):
        sent.update(json or {})
        return Response(
            {"evaluation_source": "live_datahub", "evaluation": {"verdict": "approved"}}
        )

    monkeypatch.setattr("httpx.Client.post", capture)
    monkeypatch.setenv("UNDERWRITE_REQUESTED_BY", "ci-bot")

    evaluate_deployment("http://underwrite", "urn:test", 1)

    assert sent["requested_by"] == "urn:li:corpuser:ci-bot"


def test_default_principal_is_never_anonymous(monkeypatch):
    for var in ("UNDERWRITE_REQUESTED_BY", "GITHUB_ACTOR", "GITLAB_USER_LOGIN", "BUILD_REQUESTEDFOR", "USER"):
        monkeypatch.delenv(var, raising=False)

    assert default_principal() == "urn:li:corpuser:ci-deployment-gate"


def test_schema_field_ref_resolves_to_parent_dataset():
    """Splitting on commas truncated the dataset URN into 'PROD)'."""
    field = (
        "urn:li:schemaField:(urn:li:dataset:(urn:li:dataPlatform:snowflake,"
        "raw_billing,PROD),retention_discount)"
    )

    assert dataset_urn_from_schema_field(field) == (
        "urn:li:dataset:(urn:li:dataPlatform:snowflake,raw_billing,PROD)"
    )


def test_datahub_ref_printed_for_blocked_run_is_a_resolvable_entity(capsys, monkeypatch):
    monkeypatch.setenv("UNDERWRITE_DATAHUB_UI_URL", "http://localhost:9002")
    field = (
        "urn:li:schemaField:(urn:li:dataset:(urn:li:dataPlatform:snowflake,"
        "raw_billing,PROD),retention_discount)"
    )

    exit_code = process_payload(
        "http://underwrite",
        {
            "evaluation_source": "live_datahub",
            "evaluation": {"verdict": "blocked", "reason_code": "TARGET_LEAKAGE"},
            "evidence_paths": [{"tainted_urn": field, "feature_urn": "f", "tag_found": "t"}],
            "remediation_available": False,
        },
    )
    out = capsys.readouterr().out

    assert exit_code == 1
    assert "urn:li:dataset:(urn:li:dataPlatform:snowflake,raw_billing,PROD)" in out
    assert "/dataset/PROD)" not in out


def test_entity_url_is_percent_encoded():
    url = datahub_entity_url("urn:li:dataset:(urn:li:dataPlatform:snowflake,raw_billing,PROD)")

    assert url.startswith("http://localhost:9002/dataset/urn%3Ali%3Adataset%3A")
    assert "(" not in url.split("/dataset/")[1]

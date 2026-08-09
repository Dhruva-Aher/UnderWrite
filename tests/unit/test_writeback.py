"""Unit tests for writeback operations (100% offline, zero network calls)."""

import datahub_client
from datahub_client import (
    DataHubWriteBackClient,
    plan_writeback,
    process_verdict_writeback_event,
    writeback_target_entity,
)
import datahub.metadata.schema_classes as sc
from metadata.aspects import build_documentation_mcp, build_tag_mcp
from metadata.client import MockMetadataClient
from metadata.urns import DATASET_TEST, MODEL_TEST, make_tag_urn


def test_writeback_client_tag():
    """Test tag writeback with MockMetadataClient."""
    mock = MockMetadataClient()
    client = DataHubWriteBackClient(client=mock)

    success = client.write_tag(MODEL_TEST, make_tag_urn("model-at-risk"))
    assert success is True
    assert len(mock.emitted_tags) == 1
    assert mock.emitted_tags[0]["target_urn"] == MODEL_TEST


def test_writeback_client_incident():
    """Test incident writeback with MockMetadataClient."""
    mock = MockMetadataClient()
    client = DataHubWriteBackClient(client=mock)

    success = client.write_incident(
        DATASET_TEST, MODEL_TEST, "TARGET_LEAKAGE", "Test leak description"
    )
    assert success is True
    assert len(mock.emitted_incidents) == 1
    assert mock.emitted_incidents[0]["dataset_urn"] == DATASET_TEST


def test_writeback_client_documentation():
    """Test documentation writeback with MockMetadataClient."""
    mock = MockMetadataClient()
    client = DataHubWriteBackClient(client=mock)

    success = client.write_documentation(MODEL_TEST, "BLOCKED (TARGET_LEAKAGE)")
    assert success is True
    assert len(mock.emitted_docs) == 1
    assert mock.emitted_docs[0]["target_urn"] == MODEL_TEST


def test_process_verdict_writeback_event():
    """Test event-driven writeback worker with mock client."""
    mock = MockMetadataClient()
    verdict_data = {
        "model_urn": MODEL_TEST,
        "reason_code": "TARGET_LEAKAGE",
        "verdict": "blocked",
        "headline": "Target leakage detected",
        "evidence_paths": [{"tainted_urn": DATASET_TEST}],
    }

    process_verdict_writeback_event(verdict_data, client=mock)

    assert len(mock.emitted_tags) == 1
    assert len(mock.emitted_incidents) == 1
    assert len(mock.emitted_docs) == 1


def test_api_response_shaped_writeback_is_not_skipped():
    """Regression: /evaluate schedules nested payloads; writeback must unwrap them."""
    mock = MockMetadataClient()
    model_urn = "urn:li:mlModel:(urn:li:dataPlatform:mlflow,api_shape_model,PROD)"
    api_payload = {
        "request": {
            "model_urn": model_urn,
            "gms_endpoint": "http://localhost:8080",
        },
        "evaluation": {
            "verdict": "blocked",
            "reason_code": "TARGET_LEAKAGE",
            "headline": "Blocked — a configured policy was violated.",
        },
        "evidence_paths": [
            {
                "tainted_urn": (
                    f"urn:li:schemaField:({DATASET_TEST},customer_status)"
                )
            }
        ],
        "evaluation_source": "live_datahub",
    }

    result = process_verdict_writeback_event(api_payload, client=mock)

    assert result.status == "SUCCESS"
    assert len(mock.emitted_tags) == 1
    assert mock.emitted_tags[0]["target_urn"] == model_urn
    assert len(mock.emitted_incidents) == 1
    assert mock.emitted_incidents[0]["dataset_urn"] == DATASET_TEST
    assert len(mock.emitted_docs) == 1


def test_schema_field_tainted_urn_extracts_enclosing_dataset():
    """Comma-aware extraction: dataset URNs contain commas and must not be truncated."""
    from metadata.urns import dataset_urn_from_maybe_schema_field

    field = (
        "urn:li:schemaField:(urn:li:dataset:(urn:li:dataPlatform:snowflake,"
        "raw_billing,PROD),retention_discount)"
    )
    assert dataset_urn_from_maybe_schema_field(field) == (
        "urn:li:dataset:(urn:li:dataPlatform:snowflake,raw_billing,PROD)"
    )
    assert dataset_urn_from_maybe_schema_field(DATASET_TEST) == DATASET_TEST


def _executed_operations(mock) -> set[tuple[str, str]]:
    """The (aspect, urn) pairs the executor actually emitted."""
    return (
        {("globalTags", t["target_urn"]) for t in mock.emitted_tags}
        | {("incidentInfo", i["dataset_urn"]) for i in mock.emitted_incidents}
        | {("institutionalMemory", d["target_urn"]) for d in mock.emitted_docs}
    )


def _planned_operations(plan) -> set[tuple[str, str]]:
    return {(op["aspect"], op["urn"]) for op in plan}


def test_blocked_plan_matches_operations_the_executor_actually_runs(monkeypatch):
    """The UI's write-back panel must not advertise operations that never run."""
    monkeypatch.setattr(datahub_client, "_DEDUP_CACHE", set())
    mock = MockMetadataClient()
    field = f"urn:li:schemaField:({DATASET_TEST},customer_status)"
    evidence = [{"tainted_urn": field}]

    process_verdict_writeback_event(
        {
            "model_urn": MODEL_TEST,
            "reason_code": "TARGET_LEAKAGE",
            "verdict": "blocked",
            "headline": "Target leakage detected",
            "evidence_paths": evidence,
        },
        client=mock,
    )

    plan = plan_writeback("blocked", "TARGET_LEAKAGE", MODEL_TEST, evidence)
    assert _planned_operations(plan) == _executed_operations(mock)


def test_approved_plan_matches_operations_the_executor_actually_runs(monkeypatch):
    monkeypatch.setattr(datahub_client, "_DEDUP_CACHE", set())
    mock = MockMetadataClient()

    process_verdict_writeback_event(
        {
            "model_urn": MODEL_TEST,
            "reason_code": "CLEAN",
            "verdict": "approved",
            "headline": "Approved",
        },
        client=mock,
    )

    plan = plan_writeback("approved", "CLEAN", MODEL_TEST, [])
    assert _planned_operations(plan) == _executed_operations(mock)


def test_plan_reports_incident_against_parent_dataset_not_schema_field():
    """The panel claimed a Dataset incident while showing a schemaField URN."""
    field = f"urn:li:schemaField:({DATASET_TEST},customer_status)"

    plan = plan_writeback("blocked", "TARGET_LEAKAGE", MODEL_TEST, [{"tainted_urn": field}])
    incident = next(op for op in plan if op["aspect"] == "incidentInfo")

    assert incident["urn"] == DATASET_TEST
    assert incident["entity"] == "Dataset"


def test_plan_omits_incident_when_no_evidence_entity_exists():
    plan = plan_writeback("blocked", "INCOMPLETE_LINEAGE", MODEL_TEST, [])

    assert writeback_target_entity([]) is None
    assert all(op["aspect"] != "incidentInfo" for op in plan)


def test_writeback_client_uses_explicit_gms_url(monkeypatch):
    """DataHubWriteBackClient(gms_url=...) must construct against that URL."""
    created = {}

    class FakeClient:
        def __init__(self, gms_url, token=None):
            created["gms_url"] = gms_url
            created["token"] = token

    monkeypatch.setattr("datahub_client.DataHubClient", FakeClient)
    monkeypatch.setattr("datahub_client.settings.datahub_token", "tok-xyz")

    DataHubWriteBackClient(gms_url="http://other-gms:8080")

    assert created["gms_url"] == "http://other-gms:8080"
    assert created["token"] == "tok-xyz"


def test_tag_writeback_preserves_existing_associations():
    existing = [sc.TagAssociationClass(tag="urn:li:tag:existing")]

    mcp = build_tag_mcp(MODEL_TEST, "model-at-risk", existing)

    assert {tag.tag for tag in mcp.aspect.tags} == {
        "urn:li:tag:existing",
        "urn:li:tag:model-at-risk",
    }


def test_documentation_writeback_preserves_existing_memory():
    existing = [
        sc.InstitutionalMemoryMetadataClass(
            url="https://example.test/existing",
            description="Existing audit note",
            createStamp=sc.AuditStampClass(time=1, actor="urn:li:corpuser:test"),
        )
    ]

    mcp = build_documentation_mcp(MODEL_TEST, "BLOCKED (TARGET_LEAKAGE)", existing)

    assert len(mcp.aspect.elements) == 2
    assert mcp.aspect.elements[0].description == "Existing audit note"

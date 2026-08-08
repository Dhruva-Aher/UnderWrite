"""Unit tests for writeback operations (100% offline, zero network calls)."""

from datahub_client import DataHubWriteBackClient, process_verdict_writeback_event
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
    assert len(mock.emitted_docs) == 1


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

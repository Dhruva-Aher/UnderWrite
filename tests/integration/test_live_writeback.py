"""Live integration tests for writeback operations against DataHub GMS."""

import pytest

from metadata.client import DataHubClient
from metadata.urns import DATASET_TEST, MODEL_TEST
from tests.conftest import is_gms_available

pytestmark = pytest.mark.integration

if not is_gms_available():
    pytest.skip(
        "DataHub GMS unavailable at http://localhost:8080", allow_module_level=True
    )


def test_live_writeback_operations():
    """Verify live tag, incident, and documentation writeback to GMS."""
    client = DataHubClient("http://localhost:8080")
    tag_ok = client.write_verdict_tag(MODEL_TEST, "MODEL_AT_RISK")
    inc_ok = client.write_incident(
        DATASET_TEST, MODEL_TEST, "TARGET_LEAKAGE", "Live integration test leak"
    )
    doc_ok = client.write_documentation(MODEL_TEST, "Live integration audit note")

    assert tag_ok is True
    assert inc_ok is True
    assert doc_ok is True

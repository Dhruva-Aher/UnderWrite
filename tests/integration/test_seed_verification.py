"""Live integration test for seed entity verification."""

import datahub.metadata.schema_classes as sc
import pytest

from metadata.client import DataHubClient
from metadata.urns import (
    MODEL_CHURN,
    MODEL_FRAUD,
    MODEL_REC,
)
from tests.conftest import is_gms_available

pytestmark = pytest.mark.integration

if not is_gms_available():
    pytest.skip(
        "DataHub GMS unavailable at http://localhost:8080", allow_module_level=True
    )


def test_seed_entities_exist():
    """Verify seeded ML models exist in DataHub graph."""
    client = DataHubClient("http://localhost:8080")
    for urn in [MODEL_CHURN, MODEL_REC, MODEL_FRAUD]:
        aspect = client.get_aspect(urn, sc.MLModelPropertiesClass)
        assert aspect is not None

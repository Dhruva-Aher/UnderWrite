"""Live integration tests for DataHub GMS connectivity and aspect retrieval."""

import datahub.metadata.schema_classes as sc
import pytest

from metadata.client import DataHubClient
from metadata.urns import MODEL_CHURN
from tests.conftest import is_gms_available

pytestmark = pytest.mark.integration

if not is_gms_available():
    pytest.skip(
        "DataHub GMS unavailable at http://localhost:8080", allow_module_level=True
    )


def test_live_datahub_aspect_retrieval():
    """Verify live aspect retrieval from running DataHub instance."""
    client = DataHubClient("http://localhost:8080")
    model_aspect = client.get_aspect(MODEL_CHURN, sc.MLModelPropertiesClass)
    assert model_aspect is not None
    assert model_aspect.name == "churn_model_v2"

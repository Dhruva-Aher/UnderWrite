"""Shared pytest configuration, fixtures, and GMS availability checks."""

import datahub.metadata.schema_classes as sc
import httpx
import pytest

from config import settings
from metadata.client import MockMetadataClient
from metadata.urns import (
    DATASET_RAW_BILLING,
    DATASET_TEST,
    MODEL_CHURN,
    MODEL_TEST,
)


def is_gms_available(gms_url: str = settings.gms_url) -> bool:
    """Check if DataHub GMS REST API is reachable."""
    try:
        response = httpx.get(f"{gms_url}/healthcheck", timeout=1.0)
        return response.status_code == 200
    except httpx.HTTPError:
        return False


@pytest.fixture
def mock_client() -> MockMetadataClient:
    """Provide pre-populated MockMetadataClient for zero-network unit tests."""
    seeded_aspects = {
        MODEL_CHURN: {
            sc.MLModelPropertiesClass: sc.MLModelPropertiesClass(
                name="churn_model_v2",
                mlFeatures=[
                    "urn:li:mlFeature:(urn:li:mlModel:(urn:li:dataPlatform:mlflow,churn_model_v2,PROD),monthly_charges)"
                ],
            )
        },
        "urn:li:mlFeature:(urn:li:mlModel:(urn:li:dataPlatform:mlflow,churn_model_v2,PROD),monthly_charges)": {
            sc.MLFeaturePropertiesClass: sc.MLFeaturePropertiesClass(
                sources=[DATASET_RAW_BILLING]
            )
        },
        DATASET_RAW_BILLING: {
            sc.DatasetPropertiesClass: sc.DatasetPropertiesClass(
                name="raw_billing"
            ),
            sc.GlobalTagsClass: sc.GlobalTagsClass(
                tags=[sc.TagAssociationClass(tag="urn:li:tag:post_outcome")]
            ),
            sc.UpstreamLineageClass: sc.UpstreamLineageClass(upstreams=[]),
        },
        MODEL_TEST: {
            sc.MLModelPropertiesClass: sc.MLModelPropertiesClass(
                name="test_model_v1",
                mlFeatures=[],
            )
        },
        DATASET_TEST: {
            sc.DatasetPropertiesClass: sc.DatasetPropertiesClass(
                name="test_dataset_v1"
            ),
            sc.GlobalTagsClass: sc.GlobalTagsClass(tags=[]),
        },
    }
    return MockMetadataClient(seeded_aspects=seeded_aspects)

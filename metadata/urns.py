"""URN construction helpers and metadata constants."""

from datahub.emitter.mce_builder import (
    make_dataset_urn as _make_dataset_urn,
)
from datahub.emitter.mce_builder import (
    make_ml_model_urn as _make_ml_model_urn,
)
from datahub.emitter.mce_builder import (
    make_tag_urn as _make_tag_urn,
)


# Standardized URN Builders
def make_ml_model_urn(
    model_name: str, platform: str = "mlflow", env: str = "PROD"
) -> str:
    """Generate canonical ML Model URN."""
    return _make_ml_model_urn(platform, model_name, env)


def make_dataset_urn(
    dataset_name: str, platform: str = "snowflake", env: str = "PROD"
) -> str:
    """Generate canonical Dataset URN."""
    return _make_dataset_urn(platform=platform, name=dataset_name, env=env)


def make_tag_urn(tag_name: str) -> str:
    """Generate canonical Tag URN."""
    return _make_tag_urn(tag_name)


# Pre-defined Domain Constants
MODEL_CHURN = make_ml_model_urn("churn_model_v2")
MODEL_REC = make_ml_model_urn("recommendation_model_v1")
MODEL_FRAUD = make_ml_model_urn("fraud_model_v3")
MODEL_TEST = make_ml_model_urn("test_model_v1")

DATASET_RAW_BILLING = make_dataset_urn("raw_billing")
DATASET_CUSTOMER_PROFILES = make_dataset_urn("customer_profiles")
DATASET_BILLING_CLEAN = make_dataset_urn("billing_clean")
DATASET_FEATURES_ENG = make_dataset_urn("engineered_features_v1")
DATASET_TEST = make_dataset_urn("test_dataset_v1")

TAG_MODEL_APPROVED = "MODEL_APPROVED"
TAG_MODEL_AT_RISK = "MODEL_AT_RISK"
TAG_MODEL_QUARANTINED = "MODEL_QUARANTINED"

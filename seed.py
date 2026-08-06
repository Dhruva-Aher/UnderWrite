"""
Underwrite — Canonical Seed Script (seed.py)

Ingests the 3 deterministic demo scenarios into DataHub:

1. Scenario 1 (churn_model_v2):
   - Model: churn_model_v2
   - Features: tenure_months, login_frequency, discount_history
   - Leak Path: raw_billing.retention_discount (tagged 'post_outcome') -> stg_billing -> customer_features.discount_history -> churn_model_v2
   - Expected Verdict: BLOCKED (Structural Target Leakage)

2. Scenario 2 (recommendation_model_v1):
   - Model: recommendation_model_v1
   - Features: pages_viewed_7d, avg_session_sec, click_depth
   - Clean Path: raw_clickstream -> stg_clicks -> engagement_features -> recommendation_model_v1
   - Expected Verdict: APPROVED (Clean Lineage)

3. Scenario 3 (fraud_model_v3):
   - Model: fraud_model_v3
   - Features: transaction_velocity, ip_reputation_score
   - Broken Path: risk_features lineage terminates at untracked source
   - Expected Verdict: BLOCKED (Incomplete Lineage / Fail-Closed)

Implementation Pattern:
- Uses official DataHub canonical URN builders (datahub.emitter.mce_builder)
- Emits MetadataChangeProposalWrapper via DatahubRestEmitter
- Pre-creates tag definitions ('model-at-risk', 'model-approved', 'post_outcome')
"""

import logging
import os

import datahub.metadata.schema_classes as sc
from datahub.emitter.mce_builder import (
    make_dataset_urn,
    make_global_tag_aspect_with_tag_list,
    make_ml_feature_table_urn,
    make_ml_feature_urn,
    make_ml_model_deployment_urn,
    make_ml_model_urn,
    make_schema_field_urn,
    make_tag_urn,
)
from datahub.emitter.mcp import MetadataChangeProposalWrapper
from datahub.emitter.rest_emitter import DatahubRestEmitter

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger("underwrite.seed")

GMS_URL = os.getenv("UNDERWRITE_GMS_URL", "http://localhost:8080")

# ---------------------------------------------------------------------------
# Canonical URN Constants (Built using official mce_builder helpers)
# ---------------------------------------------------------------------------

ENV = "PROD"
PLATFORM_SNOWFLAKE = "snowflake"
PLATFORM_MLFLOW = "mlflow"

# Tags
TAG_MODEL_AT_RISK = make_tag_urn("model-at-risk")
TAG_MODEL_APPROVED = make_tag_urn("model-approved")
TAG_POST_OUTCOME = make_tag_urn("post_outcome")

# Scenario 1 URNs
DATASET_RAW_CUSTOMERS = make_dataset_urn(PLATFORM_SNOWFLAKE, "raw_customers", ENV)
DATASET_RAW_BILLING = make_dataset_urn(PLATFORM_SNOWFLAKE, "raw_billing", ENV)
DATASET_STG_CUSTOMERS = make_dataset_urn(PLATFORM_SNOWFLAKE, "stg_customers", ENV)
DATASET_STG_BILLING = make_dataset_urn(PLATFORM_SNOWFLAKE, "stg_billing", ENV)

FT_CUSTOMER_FEATURES = make_ml_feature_table_urn(
    PLATFORM_SNOWFLAKE, "customer_features"
)
FEAT_TENURE = make_ml_feature_urn("customer_features", "tenure_months")
FEAT_LOGIN_FREQ = make_ml_feature_urn("customer_features", "login_frequency")
FEAT_DISCOUNT_HIST = make_ml_feature_urn("customer_features", "discount_history")

MODEL_CHURN = make_ml_model_urn(PLATFORM_MLFLOW, "churn_model_v2", ENV)
MODEL_CHURN_FIXED = make_ml_model_urn(PLATFORM_MLFLOW, "churn_model_v2_fixed", ENV)
DEPLOYMENT_CHURN = make_ml_model_deployment_urn(
    PLATFORM_MLFLOW, "churn-predictor-prod", ENV
)

# Scenario 2 URNs
DATASET_RAW_CLICKSTREAM = make_dataset_urn(PLATFORM_SNOWFLAKE, "raw_clickstream", ENV)
DATASET_STG_CLICKS = make_dataset_urn(PLATFORM_SNOWFLAKE, "stg_clicks", ENV)

FT_ENGAGEMENT_FEATURES = make_ml_feature_table_urn(
    PLATFORM_SNOWFLAKE, "engagement_features"
)
FEAT_PAGES_VIEWED = make_ml_feature_urn("engagement_features", "pages_viewed_7d")
FEAT_AVG_SESSION = make_ml_feature_urn("engagement_features", "avg_session_sec")
FEAT_CLICK_DEPTH = make_ml_feature_urn("engagement_features", "click_depth")

MODEL_REC = make_ml_model_urn(PLATFORM_MLFLOW, "recommendation_model_v1", ENV)
DEPLOYMENT_REC = make_ml_model_deployment_urn(PLATFORM_MLFLOW, "rec-engine-prod", ENV)

# Scenario 3 URNs
FT_RISK_FEATURES = make_ml_feature_table_urn(PLATFORM_SNOWFLAKE, "risk_features")
FEAT_TX_VELOCITY = make_ml_feature_urn("risk_features", "transaction_velocity")
FEAT_IP_REP = make_ml_feature_urn("risk_features", "ip_reputation_score")

MODEL_FRAUD = make_ml_model_urn(PLATFORM_MLFLOW, "fraud_model_v3", ENV)
DEPLOYMENT_FRAUD = make_ml_model_deployment_urn(
    PLATFORM_MLFLOW, "fraud-detector-staging", ENV
)


def seed_datahub(emitter: DatahubRestEmitter) -> None:
    """Emit all entities, aspects, lineage relationships, and tags for 3 scenarios."""
    logger.info("Starting DataHub seed ingestion...")

    # =========================================================================
    # 0. Tag Definitions
    # =========================================================================
    for tag_urn, name, desc in [
        (
            TAG_MODEL_AT_RISK,
            "model-at-risk",
            "Underwrite Flag: Model deployment blocked due to governance failure",
        ),
        (
            TAG_MODEL_APPROVED,
            "model-approved",
            "Underwrite Flag: Model cleared for production deployment",
        ),
        (
            TAG_POST_OUTCOME,
            "post_outcome",
            "Data Quality Flag: Target variable or post-outcome leakage column",
        ),
    ]:
        tag_prop = sc.TagPropertiesClass(name=name, description=desc)
        emitter.emit(MetadataChangeProposalWrapper(entityUrn=tag_urn, aspect=tag_prop))
    logger.info("✔ Pre-created Tag definitions")

    # =========================================================================
    # SCENARIO 1: churn_model_v2 (Structural Target Leakage — BLOCKED)
    # =========================================================================
    # Raw billing dataset + post_outcome tag on column retention_discount
    billing_prop = sc.DatasetPropertiesClass(
        name="raw_billing",
        description="Customer billing and retention discount history",
    )
    emitter.emit(
        MetadataChangeProposalWrapper(
            entityUrn=DATASET_RAW_BILLING, aspect=billing_prop
        )
    )

    billing_tags = make_global_tag_aspect_with_tag_list([TAG_POST_OUTCOME])
    emitter.emit(
        MetadataChangeProposalWrapper(
            entityUrn=make_schema_field_urn(
                DATASET_RAW_BILLING, "retention_discount"
            ),
            aspect=billing_tags,
        )
    )

    # stg_billing dataset + lineage from raw_billing
    stg_billing_prop = sc.DatasetPropertiesClass(
        name="stg_billing", description="Staging billing table"
    )
    emitter.emit(
        MetadataChangeProposalWrapper(
            entityUrn=DATASET_STG_BILLING, aspect=stg_billing_prop
        )
    )

    fg_billing = sc.FineGrainedLineageClass(
        upstreamType=sc.FineGrainedLineageUpstreamTypeClass.FIELD_SET,
        upstreams=[make_schema_field_urn(DATASET_RAW_BILLING, "retention_discount")],
        downstreamType=sc.FineGrainedLineageDownstreamTypeClass.FIELD,
        downstreams=[make_schema_field_urn(DATASET_STG_BILLING, "discount_history")],
    )
    stg_billing_lineage = sc.UpstreamLineageClass(
        upstreams=[
            sc.UpstreamClass(
                dataset=DATASET_RAW_BILLING, type=sc.DatasetLineageTypeClass.TRANSFORMED
            )
        ],
        fineGrainedLineages=[fg_billing],
    )
    emitter.emit(
        MetadataChangeProposalWrapper(
            entityUrn=DATASET_STG_BILLING, aspect=stg_billing_lineage
        )
    )

    # raw_customers & stg_customers
    cust_prop = sc.DatasetPropertiesClass(
        name="raw_customers", description="Raw customer accounts"
    )
    emitter.emit(
        MetadataChangeProposalWrapper(entityUrn=DATASET_RAW_CUSTOMERS, aspect=cust_prop)
    )

    stg_cust_prop = sc.DatasetPropertiesClass(
        name="stg_customers", description="Staging customer table"
    )
    emitter.emit(
        MetadataChangeProposalWrapper(
            entityUrn=DATASET_STG_CUSTOMERS, aspect=stg_cust_prop
        )
    )

    stg_cust_lineage = sc.UpstreamLineageClass(
        upstreams=[
            sc.UpstreamClass(
                dataset=DATASET_RAW_CUSTOMERS,
                type=sc.DatasetLineageTypeClass.TRANSFORMED,
            )
        ]
    )
    emitter.emit(
        MetadataChangeProposalWrapper(
            entityUrn=DATASET_STG_CUSTOMERS, aspect=stg_cust_lineage
        )
    )

    # customer_features Table & MLFeatures
    ft_cust_prop = sc.MLFeatureTablePropertiesClass(
        description="Customer churn feature store table",
        mlFeatures=[FEAT_TENURE, FEAT_LOGIN_FREQ, FEAT_DISCOUNT_HIST],
    )
    emitter.emit(
        MetadataChangeProposalWrapper(
            entityUrn=FT_CUSTOMER_FEATURES, aspect=ft_cust_prop
        )
    )

    feat_tenure_prop = sc.MLFeaturePropertiesClass(
        description="Months active", sources=[DATASET_STG_CUSTOMERS]
    )
    emitter.emit(
        MetadataChangeProposalWrapper(entityUrn=FEAT_TENURE, aspect=feat_tenure_prop)
    )

    feat_login_prop = sc.MLFeaturePropertiesClass(
        description="Logins in past 30d", sources=[DATASET_STG_CUSTOMERS]
    )
    emitter.emit(
        MetadataChangeProposalWrapper(entityUrn=FEAT_LOGIN_FREQ, aspect=feat_login_prop)
    )

    feat_discount_prop = sc.MLFeaturePropertiesClass(
        description="Historical discounts applied", sources=[DATASET_STG_BILLING]
    )
    emitter.emit(
        MetadataChangeProposalWrapper(
            entityUrn=FEAT_DISCOUNT_HIST, aspect=feat_discount_prop
        )
    )

    # churn_model_v2 & churn-predictor-prod
    model_churn_prop = sc.MLModelPropertiesClass(
        name="churn_model_v2",
        description="Customer churn predictor model v2",
        mlFeatures=[FEAT_TENURE, FEAT_LOGIN_FREQ, FEAT_DISCOUNT_HIST],
        deployments=[DEPLOYMENT_CHURN],
    )
    emitter.emit(
        MetadataChangeProposalWrapper(entityUrn=MODEL_CHURN, aspect=model_churn_prop)
    )

    dep_churn_prop = sc.MLModelDeploymentPropertiesClass(
        description="Production churn scoring service",
        status=sc.DeploymentStatusClass.IN_SERVICE,
    )
    emitter.emit(
        MetadataChangeProposalWrapper(entityUrn=DEPLOYMENT_CHURN, aspect=dep_churn_prop)
    )

    logger.info("✔ Ingested Scenario 1 (churn_model_v2 - Leakage)")

    # Remediated churn model: only the independently sourced tenure feature is
    # retained, so it exists as a real selectable clean demo entity.
    model_churn_fixed_prop = sc.MLModelPropertiesClass(
        name="churn_model_v2_fixed",
        description="Remediated customer churn predictor without discount history",
        mlFeatures=[FEAT_TENURE],
    )
    emitter.emit(
        MetadataChangeProposalWrapper(
            entityUrn=MODEL_CHURN_FIXED, aspect=model_churn_fixed_prop
        )
    )
    logger.info("✔ Ingested remediated churn_model_v2_fixed")

    # =========================================================================
    # SCENARIO 2: recommendation_model_v1 (Clean Lineage — APPROVED)
    # =========================================================================
    raw_clicks_prop = sc.DatasetPropertiesClass(
        name="raw_clickstream", description="User click events"
    )
    emitter.emit(
        MetadataChangeProposalWrapper(
            entityUrn=DATASET_RAW_CLICKSTREAM, aspect=raw_clicks_prop
        )
    )

    stg_clicks_prop = sc.DatasetPropertiesClass(
        name="stg_clicks", description="Staging clickstream metrics"
    )
    emitter.emit(
        MetadataChangeProposalWrapper(
            entityUrn=DATASET_STG_CLICKS, aspect=stg_clicks_prop
        )
    )

    stg_clicks_lineage = sc.UpstreamLineageClass(
        upstreams=[
            sc.UpstreamClass(
                dataset=DATASET_RAW_CLICKSTREAM,
                type=sc.DatasetLineageTypeClass.TRANSFORMED,
            )
        ]
    )
    emitter.emit(
        MetadataChangeProposalWrapper(
            entityUrn=DATASET_STG_CLICKS, aspect=stg_clicks_lineage
        )
    )

    ft_eng_prop = sc.MLFeatureTablePropertiesClass(
        description="User engagement features",
        mlFeatures=[FEAT_PAGES_VIEWED, FEAT_AVG_SESSION, FEAT_CLICK_DEPTH],
    )
    emitter.emit(
        MetadataChangeProposalWrapper(
            entityUrn=FT_ENGAGEMENT_FEATURES, aspect=ft_eng_prop
        )
    )

    for feat_urn, name in [
        (FEAT_PAGES_VIEWED, "pages_viewed_7d"),
        (FEAT_AVG_SESSION, "avg_session_sec"),
        (FEAT_CLICK_DEPTH, "click_depth"),
    ]:
        f_prop = sc.MLFeaturePropertiesClass(
            description=f"Feature {name}", sources=[DATASET_STG_CLICKS]
        )
        emitter.emit(MetadataChangeProposalWrapper(entityUrn=feat_urn, aspect=f_prop))

    model_rec_prop = sc.MLModelPropertiesClass(
        name="recommendation_model_v1",
        description="Personalized recommendation engine v1",
        mlFeatures=[FEAT_PAGES_VIEWED, FEAT_AVG_SESSION, FEAT_CLICK_DEPTH],
        deployments=[DEPLOYMENT_REC],
    )
    emitter.emit(
        MetadataChangeProposalWrapper(entityUrn=MODEL_REC, aspect=model_rec_prop)
    )

    dep_rec_prop = sc.MLModelDeploymentPropertiesClass(
        description="Production rec service", status=sc.DeploymentStatusClass.IN_SERVICE
    )
    emitter.emit(
        MetadataChangeProposalWrapper(entityUrn=DEPLOYMENT_REC, aspect=dep_rec_prop)
    )

    logger.info("✔ Ingested Scenario 2 (recommendation_model_v1 - Clean)")

    # =========================================================================
    # SCENARIO 3: fraud_model_v3 (Incomplete Lineage — BLOCKED)
    # =========================================================================
    # risk_features has features, but sources point to no registered dataset (lineage terminates)
    ft_risk_prop = sc.MLFeatureTablePropertiesClass(
        description="Transaction risk features",
        mlFeatures=[FEAT_TX_VELOCITY, FEAT_IP_REP],
    )
    emitter.emit(
        MetadataChangeProposalWrapper(entityUrn=FT_RISK_FEATURES, aspect=ft_risk_prop)
    )

    # Intentionally empty sources list to simulate incomplete lineage provenance gap
    for feat_urn, name in [
        (FEAT_TX_VELOCITY, "transaction_velocity"),
        (FEAT_IP_REP, "ip_reputation_score"),
    ]:
        f_prop = sc.MLFeaturePropertiesClass(
            description=f"Feature {name} (unresolved upstream)", sources=[]
        )
        emitter.emit(MetadataChangeProposalWrapper(entityUrn=feat_urn, aspect=f_prop))

    model_fraud_prop = sc.MLModelPropertiesClass(
        name="fraud_model_v3",
        description="Real-time fraud detector model v3",
        mlFeatures=[FEAT_TX_VELOCITY, FEAT_IP_REP],
        deployments=[DEPLOYMENT_FRAUD],
    )
    emitter.emit(
        MetadataChangeProposalWrapper(entityUrn=MODEL_FRAUD, aspect=model_fraud_prop)
    )

    dep_fraud_prop = sc.MLModelDeploymentPropertiesClass(
        description="Staging fraud service", status=sc.DeploymentStatusClass.CREATING
    )
    emitter.emit(
        MetadataChangeProposalWrapper(entityUrn=DEPLOYMENT_FRAUD, aspect=dep_fraud_prop)
    )

    logger.info("✔ Ingested Scenario 3 (fraud_model_v3 - Incomplete Lineage)")
    logger.info("🎉 DataHub seed ingestion completed successfully!")


if __name__ == "__main__":
    emitter = DatahubRestEmitter(GMS_URL)
    seed_datahub(emitter)

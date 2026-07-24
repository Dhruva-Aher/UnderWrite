"""Unit tests for Agent engine and PolicyEvaluator (100% offline, zero network calls)."""

import datahub.metadata.schema_classes as sc
import pytest

from agent import (
    Agent,
    InternalGraph,
    PolicyEvaluator,
    load_policies_from_yaml,
    normalize_to_internal_graph,
)
from config import Settings
from metadata.client import MockMetadataClient
from metadata.urns import (
    DATASET_RAW_BILLING,
    MODEL_CHURN,
    make_dataset_urn,
    make_ml_model_urn,
)


def test_agent_evaluate_target_leakage(mock_client: MockMetadataClient):
    """Test Agent detecting target leakage via MockMetadataClient."""
    agent = Agent(client=mock_client)
    verdict = agent.evaluate_model(MODEL_CHURN)

    assert verdict.verdict == "blocked"
    assert verdict.reason_code == "TARGET_LEAKAGE"
    assert len(verdict.evidence_paths) == 1
    assert verdict.evidence_paths[0].tainted_urn == DATASET_RAW_BILLING


def test_missing_dataset_properties_fails_closed(mock_client: MockMetadataClient):
    """A referenced dataset without metadata must never be treated as a leaf."""
    feature_urn = "urn:li:mlFeature:(model,missing_dataset_feature)"
    dataset_urn = "urn:li:dataset:(urn:li:dataPlatform:snowflake,missing,PROD)"
    mock_client.aspects[MODEL_CHURN][sc.MLModelPropertiesClass].mlFeatures = [feature_urn]
    mock_client.aspects[feature_urn] = {
        sc.MLFeaturePropertiesClass: sc.MLFeaturePropertiesClass(sources=[dataset_urn])
    }

    verdict = Agent(mock_client).evaluate_model(MODEL_CHURN)

    assert verdict.verdict == "blocked"
    assert verdict.reason_code == "INCOMPLETE_LINEAGE"


def test_depth_limit_fails_closed():
    graph = InternalGraph()
    root = "model"
    graph.add_node(root, "mlModel", root)
    previous = root
    for index in range(8):
        urn = f"dataset-{index}"
        graph.add_node(urn, "dataset", urn)
        graph.add_edge(previous, urn)
        previous = urn

    verdict = PolicyEvaluator().evaluate(graph, root)

    assert verdict.verdict == "blocked"
    assert verdict.reason_code == "INCOMPLETE_LINEAGE"


def test_model_without_features_fails_closed(mock_client: MockMetadataClient):
    mock_client.aspects[MODEL_CHURN][sc.MLModelPropertiesClass].mlFeatures = []

    verdict = Agent(mock_client).evaluate_model(MODEL_CHURN)

    assert verdict.verdict == "blocked"
    assert verdict.reason_code == "INCOMPLETE_LINEAGE"


def test_agent_evaluate_clean_model(mock_client: MockMetadataClient):
    """Test Agent approving a clean model with no leak tags."""
    clean_model_urn = make_ml_model_urn("clean_model_v1")
    clean_feat_urn = f"urn:li:mlFeature:({clean_model_urn},clean_feature)"
    clean_ds_urn = make_dataset_urn("clean_dataset")

    mock_client.aspects[clean_model_urn] = {
        sc.MLModelPropertiesClass: sc.MLModelPropertiesClass(
            name="clean_model_v1", mlFeatures=[clean_feat_urn]
        )
    }
    mock_client.aspects[clean_feat_urn] = {
        sc.MLFeaturePropertiesClass: sc.MLFeaturePropertiesClass(sources=[clean_ds_urn])
    }
    mock_client.aspects[clean_ds_urn] = {
        sc.DatasetPropertiesClass: sc.DatasetPropertiesClass(name="clean_dataset"),
        sc.GlobalTagsClass: sc.GlobalTagsClass(tags=[]),
    }

    agent = Agent(client=mock_client)
    verdict = agent.evaluate_model(clean_model_urn)

    assert verdict.verdict == "approved"
    assert verdict.reason_code == "CLEAN"
    assert len(verdict.evidence_paths) == 0


def test_agent_incomplete_lineage(mock_client: MockMetadataClient):
    """Test Agent detecting incomplete lineage when feature source is missing."""
    inc_model_urn = make_ml_model_urn("inc_model_v1")
    inc_feat_urn = f"urn:li:mlFeature:({inc_model_urn},inc_feature)"

    mock_client.aspects[inc_model_urn] = {
        sc.MLModelPropertiesClass: sc.MLModelPropertiesClass(
            name="inc_model_v1", mlFeatures=[inc_feat_urn]
        )
    }
    mock_client.aspects[inc_feat_urn] = {
        sc.MLFeaturePropertiesClass: sc.MLFeaturePropertiesClass(sources=[])
    }

    agent = Agent(client=mock_client)
    verdict = agent.evaluate_model(inc_model_urn)

    assert verdict.verdict == "blocked"
    assert verdict.reason_code == "INCOMPLETE_LINEAGE"


def test_internal_graph_normalization():
    """Test graph normalization logic."""
    acquired = {
        "model_urn": "urn:test",
        "model_props": sc.MLModelPropertiesClass(name="test", mlFeatures=[]),
        "features_data": {},
        "datasets_data": {},
    }
    ig = normalize_to_internal_graph(acquired)
    assert "urn:test" in ig.nodes
    assert ig.nodes["urn:test"].type == "mlModel"


def test_agent_evaluates_all_enabled_policies(mock_client, tmp_path):
    """A later enabled policy must not be silently ignored."""
    policy_file = tmp_path / "policies.yaml"
    policy_file.write_text(
        """policies:
  - id: FIRST
    target_tags: [is_target]
  - id: SECOND
    target_tags: [post_outcome]
"""
    )

    verdict = Agent(
        client=mock_client, settings=Settings(policy_path=str(policy_file))
    ).evaluate_model(MODEL_CHURN)

    assert verdict.verdict == "blocked"
    assert verdict.reason_code == "POLICY_VIOLATION:SECOND"
    assert verdict.evidence_paths[0].policy_id == "SECOND"


@pytest.mark.parametrize(
    "content",
    ["[]\n", "policies:\n  - id: DUP\n  - id: DUP\n"],
)
def test_invalid_policy_configuration_falls_back_to_default(content, tmp_path):
    """Malformed or duplicate policy configuration cannot disable enforcement."""
    policy_file = tmp_path / "policies.yaml"
    policy_file.write_text(content)

    policies = load_policies_from_yaml(str(policy_file))

    assert [policy.policy_id for policy in policies] == ["ML-LEAK-001"]

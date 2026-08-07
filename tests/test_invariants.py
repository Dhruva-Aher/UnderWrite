"""Tests for Underwrite Invariants."""
import pytest
from agent import Agent
from metadata.client import MockMetadataClient
from config import Settings
from exceptions import UnderwriteError, PolicyConfigurationError
from constants import ReasonCode, Verdict

def test_datahub_unavailable_blocks_deployment():
    # If the metadata client cannot provide a graph or throws an error
    # It should result in a blocked verdict
    client = MockMetadataClient() # Empty mock
    settings = Settings(datahub_token="dummy", gms_url="dummy")
    agent = Agent(client=client, settings=settings)
    
    verdict = agent.evaluate_model("urn:li:mlModel:(urn:li:dataPlatform:mlflow,model1,PROD)")
    assert verdict.verdict == Verdict.BLOCKED
    assert verdict.reason_code == ReasonCode.INCOMPLETE_LINEAGE

def test_policy_violation_blocks_deployment():
    # Simulate a graph with target leakage
    client = MockMetadataClient.load_fixture("demo/fixtures/target_leakage_metadata.json")
    settings = Settings(datahub_token="dummy", gms_url="dummy")
    agent = Agent(client=client, settings=settings)
    
    verdict = agent.evaluate_model("urn:li:mlModel:(urn:li:dataPlatform:mlflow,churn_model_v2,PROD)")
    assert verdict.verdict == Verdict.BLOCKED
    assert verdict.reason_code == ReasonCode.TARGET_LEAKAGE

def test_clean_graph_allows_deployment():
    client = MockMetadataClient.load_fixture("demo/fixtures/clean_metadata.json")
    settings = Settings(datahub_token="dummy", gms_url="dummy")
    agent = Agent(client=client, settings=settings)
    
    verdict = agent.evaluate_model("urn:li:mlModel:(urn:li:dataPlatform:mlflow,churn_model_v2,PROD)")
    assert verdict.verdict == Verdict.APPROVED
    assert verdict.reason_code == ReasonCode.CLEAN

def test_corrupt_policy_configuration():
    from agent import load_policies_from_yaml
    # A corrupt YAML file should raise PolicyConfigurationError at startup
    with open("tests/corrupt.yaml", "w") as f:
        f.write("invalid: yaml: :")
    
    with pytest.raises(PolicyConfigurationError):
        load_policies_from_yaml("tests/corrupt.yaml")

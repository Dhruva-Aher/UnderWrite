"""Tests for Remediation Engine (Milestone 2A)."""

import pytest
from unittest.mock import patch, MagicMock

from agent import InternalGraph, VerdictInternal, EvidencePath, Node
from remediation_engine import generate_and_verify_hypothesis, ProposedPatch, verify_hypothesis, PatchVerificationInput

@pytest.fixture
def mock_graph():
    ig = InternalGraph()
    ig.add_node("root_model", "mlModel", "root_model")
    ig.add_node("feature_a", "mlFeature", "feature_a")
    ig.add_node("dataset_b", "dataset", "dataset_b", tags={"urn:li:tag:post_outcome"})
    ig.add_edge("root_model", "feature_a", "CONSUMES")
    ig.add_edge("feature_a", "dataset_b", "DERIVED_FROM")
    # Add adjacent dictionary explicitly for tests if needed, though add_edge does this
    return ig

@pytest.fixture
def mock_verdict():
    ep = EvidencePath(
        feature_urn="feature_a",
        tainted_urn="dataset_b",
        tag_found="urn:li:tag:post_outcome",
        path=["root_model", "feature_a", "dataset_b"],
        policy_id="ML-LEAK-001"
    )
    return VerdictInternal(
        model_urn="root_model",
        verdict="blocked",
        reason_code="TARGET_LEAKAGE",
        evidence_paths=[ep]
    )

def test_verify_hypothesis_success(mock_graph):
    # Severing dataset_b should remove the leak
    input_obj = PatchVerificationInput(
        original_evidence=[EvidencePath(feature_urn="feature_a", tainted_urn="dataset_b", tag_found="urn:li:tag:post_outcome", path=[Node(urn="dataset_b", type="dataset", name="b", description="", tags=set())], policy_id="test")],
        patch=ProposedPatch(file_path="", search_text="", replace_text="-- dataset_b", rationale="")
    )
    new_verdict = verify_hypothesis(mock_graph, "root_model", input_obj)
    assert new_verdict.verdict == "approved"
    assert new_verdict.reason_code == "CLEAN"

def test_verify_hypothesis_failure(mock_graph):
    # Severing an unrelated node shouldn't fix the leak
    input_obj = PatchVerificationInput(
        original_evidence=[EvidencePath(feature_urn="feature_a", tainted_urn="dataset_b", tag_found="urn:li:tag:post_outcome", path=[Node(urn="dataset_b", type="dataset", name="b", description="", tags=set())], policy_id="test")],
        patch=ProposedPatch(file_path="", search_text="", replace_text="-- unrelated", rationale="")
    )
    new_verdict = verify_hypothesis(mock_graph, "root_model", input_obj)
    assert new_verdict.verdict == "blocked"
    assert new_verdict.reason_code == "TARGET_LEAKAGE"

@patch("remediation_engine.get_llm")
def test_generate_and_verify_hypothesis_success(mock_get_llm, mock_verdict, mock_graph):
    mock_llm = MagicMock()
    mock_get_llm.return_value = mock_llm
    
    mock_chain = MagicMock()
    mock_chain.invoke.return_value = ProposedPatch(
        file_path="model.sql",
        search_text="SELECT *",
        replace_text="SELECT safe_col -- dataset_b",
        rationale="Removed leaky column"
    )

    mock_prompt = MagicMock()
    mock_prompt.__or__.return_value = mock_chain
    
    mock_langchain = MagicMock()
    mock_langchain.prompts.ChatPromptTemplate.from_messages.return_value = mock_prompt
    with patch.dict("sys.modules", {"langchain_core": mock_langchain, "langchain_core.prompts": mock_langchain.prompts}):
        result = generate_and_verify_hypothesis(mock_verdict, mock_graph)

    assert result.success is True
    assert result.patch.file_path == "model.sql"
    assert "successfully verified" in result.message

@patch("remediation_engine.get_llm")
def test_generate_and_verify_hypothesis_failure(mock_get_llm, mock_verdict, mock_graph):
    mock_llm = MagicMock()
    mock_get_llm.return_value = mock_llm
    
    mock_chain = MagicMock()
    # LLM hallucinates a URN or severs the wrong one
    mock_chain.invoke.return_value = ProposedPatch(
        file_path="model.sql",
        search_text="SELECT *",
        replace_text="SELECT safe_col",
        rationale="Removed wrong column"
    )

    mock_prompt = MagicMock()
    mock_prompt.__or__.return_value = mock_chain
    
    mock_langchain = MagicMock()
    mock_langchain.prompts.ChatPromptTemplate.from_messages.return_value = mock_prompt
    with patch.dict("sys.modules", {"langchain_core": mock_langchain, "langchain_core.prompts": mock_langchain.prompts}):
        result = generate_and_verify_hypothesis(mock_verdict, mock_graph)

    assert result.success is False
    assert len(result.failure_evidence) > 0
    assert result.failure_evidence[0].tainted_urn == "dataset_b"
    assert "failed after 3 attempts" in result.message
    
    assert result.investigation_report is not None
    assert len(result.investigation_report.attempts) == 3
    assert result.investigation_report.policy == "TARGET_LEAKAGE"

@patch("remediation_engine.get_llm")
def test_generate_and_verify_hypothesis_first_fail_then_success(mock_get_llm, mock_verdict, mock_graph):
    mock_llm = MagicMock()
    mock_get_llm.return_value = mock_llm
    
    mock_chain = MagicMock()
    # First invoke returns a bad patch, second returns a good patch
    mock_chain.invoke.side_effect = [
        ProposedPatch(
            file_path="model.sql",
            search_text="SELECT *",
            replace_text="SELECT safe_col -- wrong_urn",
            rationale="Removed wrong column"
        ),
        ProposedPatch(
            file_path="model.sql",
            search_text="SELECT *",
            replace_text="SELECT safe_col -- dataset_b",
            rationale="Removed leaky column"
        )
    ]

    mock_prompt = MagicMock()
    mock_prompt.__or__.return_value = mock_chain
    
    mock_langchain = MagicMock()
    mock_langchain.prompts.ChatPromptTemplate.from_messages.return_value = mock_prompt
    with patch.dict("sys.modules", {"langchain_core": mock_langchain, "langchain_core.prompts": mock_langchain.prompts}):
        result = generate_and_verify_hypothesis(mock_verdict, mock_graph)

    assert result.success is True
    assert "attempt 2" in result.message

@patch("remediation_engine.get_llm")
def test_generate_and_verify_hypothesis_exception(mock_get_llm, mock_verdict, mock_graph):
    mock_llm = MagicMock()
    mock_get_llm.return_value = mock_llm
    
    mock_chain = MagicMock()
    # Simulate LLM returning malformed JSON causing an exception
    mock_chain.invoke.side_effect = Exception("Malformed JSON")

    mock_prompt = MagicMock()
    mock_prompt.__or__.return_value = mock_chain
    
    mock_langchain = MagicMock()
    mock_langchain.prompts.ChatPromptTemplate.from_messages.return_value = mock_prompt
    with patch.dict("sys.modules", {"langchain_core": mock_langchain, "langchain_core.prompts": mock_langchain.prompts}):
        result = generate_and_verify_hypothesis(mock_verdict, mock_graph)

    assert result.success is False
    assert result.patch is None
    assert "exception" in result.message
    
    assert result.investigation_report is not None
    assert len(result.investigation_report.attempts) == 0
    assert "Malformed JSON" in result.investigation_report.verification_summary

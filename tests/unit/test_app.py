"""API boundary validation tests."""

from fastapi.testclient import TestClient

import app
from agent import InternalGraph, Policy, PolicyEvaluator
from metadata.client import DataHubClient


def test_evaluate_rejects_invalid_model_urn():
    with TestClient(app.app) as client:
        response = client.post("/evaluate", json={"model_urn": "not-a-datahub-urn"})

    assert response.status_code == 422


def test_override_rejects_invalid_model_urn_before_background_write():
    with TestClient(app.app) as client:
        response = client.post(
            "/override", json={"model_urn": "not-a-datahub-urn", "signer_name": "QA"}
        )

    assert response.status_code == 422


def test_override_is_disabled_without_a_configured_secret(monkeypatch):
    monkeypatch.setattr(app.settings, "override_token", None)

    with TestClient(app.app) as client:
        response = client.post(
            "/override",
            json={
                "model_urn": "urn:li:mlModel:(urn:li:dataPlatform:mlflow,test,PROD)",
                "signer_name": "QA",
            },
        )

    assert response.status_code == 503


def test_override_requires_the_configured_secret(monkeypatch):
    monkeypatch.setattr(app.settings, "override_token", "judge-secret")

    with TestClient(app.app) as client:
        response = client.post(
            "/override",
            json={
                "model_urn": "urn:li:mlModel:(urn:li:dataPlatform:mlflow,test,PROD)",
                "signer_name": "QA",
            },
        )

    assert response.status_code == 403


def test_cached_evaluation_never_schedules_live_writeback(monkeypatch):
    model_urn = "urn:li:mlModel:(urn:li:dataPlatform:mlflow,churn_model_v2,PROD)"
    monkeypatch.setattr(app, "get_metadata_client", lambda: None)
    scheduled = []

    class Tasks:
        def add_task(self, *args):
            scheduled.append(args)

    import asyncio

    response = asyncio.run(app.evaluate_model_route(app.EvaluateRequest(model_urn=model_urn), Tasks()))

    assert response["evaluation_source"] == "cached_fixture"
    assert scheduled == []


def test_health_check_uses_datahub_health_endpoint(monkeypatch):
    monkeypatch.setattr(DataHubClient, "is_healthy", lambda _: True)

    with TestClient(app.app) as client:
        response = client.get("/health")

    assert response.json()["mode"] == "live"


def test_every_selectable_demo_model_has_an_offline_fixture():
    selectable_models = {
        "urn:li:mlModel:(urn:li:dataPlatform:mlflow,churn_model_v2,PROD)",
        "urn:li:mlModel:(urn:li:dataPlatform:mlflow,churn_model_v2_fixed,PROD)",
        "urn:li:mlModel:(urn:li:dataPlatform:mlflow,recommendation_model_v1,PROD)",
        "urn:li:mlModel:(urn:li:dataPlatform:mlflow,fraud_model_v3,PROD)",
    }

    assert selectable_models <= app.CACHED_VERDICTS.keys()
    assert all(app.CACHED_VERDICTS[urn]["graph"]["nodes"] for urn in selectable_models)


def test_live_response_uses_serialized_live_graph_not_cached_fixture():
    graph = InternalGraph()
    model = "urn:li:mlModel:(urn:li:dataPlatform:mlflow,live_test,PROD)"
    graph.add_node(model, "mlModel", "live_test")
    verdict = PolicyEvaluator(Policy("P", "P", set(), "")).evaluate(graph, model)

    payload = app.format_verdict_response(app.EvaluateRequest(model_urn=model), "req-id", 50, verdict, graph)
    assert payload["evaluation_source"] == "live_datahub"
    assert payload["graph"]["nodes"][0]["label"] == "live_test"


def test_live_graph_uses_data_flow_direction_and_schema_field_type():
    graph = InternalGraph()
    model = "urn:li:mlModel:(urn:li:dataPlatform:mlflow,live_test,PROD)"
    field = "urn:li:schemaField:(urn:li:dataset:(urn:li:dataPlatform:snowflake,raw,PROD),field)"
    graph.add_node(model, "mlModel", "live_test")
    graph.add_node(field, "schemaField", "field")
    graph.add_edge(model, field)
    verdict = PolicyEvaluator(Policy("P", "P", set(), "")).evaluate(graph, model)

    payload = app.graph_to_ui_payload(graph, verdict)

    assert payload["edges"] == [{"from": field, "to": model, "isLeak": False, "isBroken": False}]
    assert next(node for node in payload["nodes"] if node["id"] == field)["type"] == "schema_field"


def test_policy_violation_is_not_presented_as_approved():
    graph = InternalGraph()
    model = "urn:li:mlModel:(urn:li:dataPlatform:mlflow,policy_test,PROD)"
    graph.add_node(model, "mlModel", "policy_test")
    verdict = PolicyEvaluator(Policy("P", "P", {"tag"}, "")).evaluate(graph, model)
    verdict.verdict = "blocked"
    verdict.reason_code = "POLICY_VIOLATION:P"

    payload = app.format_verdict_response(app.EvaluateRequest(model_urn=model), "req-id", 50, verdict, graph)
    assert payload["evaluation"]["verdict"] == "blocked"
    assert payload["evaluation"]["headline"] == "Blocked — a configured policy was violated."


def test_corrupt_cache_is_ignored(monkeypatch, tmp_path):
    (tmp_path / "verdicts.json").write_text("{invalid")
    monkeypatch.setattr(app, "CACHE_DIR", tmp_path)

    assert app.load_cached_verdicts() == {}

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




def test_health_check_uses_datahub_health_endpoint(monkeypatch):
    monkeypatch.setattr(DataHubClient, "is_healthy", lambda _: True)

    with TestClient(app.app) as client:
        response = client.get("/health")

    assert response.json()["mode"] == "live"


def test_live_response_uses_serialized_live_graph_not_cached_fixture():
    graph = InternalGraph()
    model = "urn:li:mlModel:(urn:li:dataPlatform:mlflow,live_test,PROD)"
    graph.add_node(model, "mlModel", "live_test")
    verdict = PolicyEvaluator(Policy("P", "P", set(), "")).evaluate(graph, model)

    payload = app.format_verdict_response(app.EvaluateRequest(model_urn=model), "req-id", 50, verdict, graph)
    assert payload["evaluation_source"] == "live_datahub"
    assert payload["graph"]["nodes"][0]["data"]["label"] == "live_test"


def test_live_graph_uses_data_flow_direction_and_schema_field_type():
    graph = InternalGraph()
    model = "urn:li:mlModel:(urn:li:dataPlatform:mlflow,live_test,PROD)"
    field = "urn:li:schemaField:(urn:li:dataset:(urn:li:dataPlatform:snowflake,raw,PROD),field)"
    graph.add_node(model, "mlModel", "live_test")
    graph.add_node(field, "schemaField", "field")
    graph.add_edge(model, field)
    verdict = PolicyEvaluator(Policy("P", "P", set(), "")).evaluate(graph, model)

    payload = app.graph_to_ui_payload(graph, verdict)

    assert len(payload["edges"]) == 1
    edge = payload["edges"][0]
    assert edge["id"] == f"e0:{field}->{model}"
    assert edge["source"] == field
    assert edge["target"] == model
    assert edge["data"] == {"isLeak": False, "isBroken": False}
    field_node = next(node for node in payload["nodes"] if node["id"] == field)
    assert field_node["data"]["type"] == "schema_field"
    # ReactFlow requires position.{x,y}; a bare x/y unmounts the whole console.
    assert set(field_node["position"]) == {"x", "y"}


def test_policy_violation_is_not_presented_as_approved():
    graph = InternalGraph()
    model = "urn:li:mlModel:(urn:li:dataPlatform:mlflow,policy_test,PROD)"
    graph.add_node(model, "mlModel", "policy_test")
    verdict = PolicyEvaluator(Policy("P", "P", {"tag"}, "")).evaluate(graph, model)
    from dataclasses import replace
    verdict = replace(verdict, verdict="blocked", reason_code="POLICY_VIOLATION:P")

    payload = app.format_verdict_response(app.EvaluateRequest(model_urn=model), "req-id", 50, verdict, graph)
    assert payload["evaluation"]["verdict"] == "blocked"
    assert payload["evaluation"]["headline"] == "Blocked — a configured policy was violated."


def test_evidence_nodes_carry_leak_styling_reactflow_can_render():
    """isLeakNode was set but nothing rendered it, so the leak path looked ordinary."""
    from dataclasses import replace

    graph = InternalGraph()
    model = "urn:li:mlModel:(urn:li:dataPlatform:mlflow,leak_test,PROD)"
    field = "urn:li:schemaField:(urn:li:dataset:(urn:li:dataPlatform:snowflake,raw,PROD),leak)"
    graph.add_node(model, "mlModel", "leak_test")
    graph.add_node(field, "schemaField", "leak")
    graph.add_edge(model, field)
    verdict = PolicyEvaluator(Policy("P", "P", set(), "")).evaluate(graph, model)

    class _Path:
        path = [model, field]

    verdict = replace(verdict, evidence_paths=[_Path()])
    payload = app.graph_to_ui_payload(graph, verdict)

    leak_node = next(n for n in payload["nodes"] if n["id"] == field)
    assert leak_node["data"]["isLeakNode"] is True
    assert leak_node["style"] == app.NODE_STYLE_LEAK
    assert payload["edges"][0]["animated"] is True
    assert payload["edges"][0]["style"]["stroke"] == "#ef4444"


def test_requesting_principal_defaults_to_a_named_actor():
    """'corpuser:unknown' in an audit trail is indistinguishable from no audit trail."""
    request = app.EvaluateRequest(
        model_urn="urn:li:mlModel:(urn:li:dataPlatform:mlflow,m,PROD)"
    )

    assert request.requested_by == "urn:li:corpuser:underwrite-agent"
    assert "unknown" not in request.requested_by


def test_writeback_status_is_pending_until_the_background_task_records_it():
    with TestClient(app.app) as client:
        response = client.get("/writeback/UW-REQ-NOTHING")

    assert response.status_code == 200
    assert response.json()["status"] == "PENDING"


def test_writeback_status_reports_the_recorded_outcome():
    app.writeback_status_store.put(
        "UW-REQ-DONE", {"status": "SUCCESS", "message": "DataHub GMS write-back complete"}
    )

    with TestClient(app.app) as client:
        body = client.get("/writeback/UW-REQ-DONE").json()

    assert body["status"] == "SUCCESS"
    assert body["request_id"] == "UW-REQ-DONE"


def test_writeback_failure_never_changes_the_verdict_already_returned(monkeypatch):
    def boom(*args, **kwargs):
        raise RuntimeError("GMS exploded")

    monkeypatch.setattr(app, "process_verdict_writeback_event", boom)

    app.run_writeback_and_record("UW-REQ-BOOM", {})

    assert app.writeback_status_store.get("UW-REQ-BOOM")["status"] == "FAILED"



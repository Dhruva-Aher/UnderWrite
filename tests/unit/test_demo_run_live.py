"""Demo orchestrator success semantics."""

from datahub_client import WritebackResult
from demo import run_demo


def test_run_live_false_when_writeback_incomplete(monkeypatch):
    class Healthy:
        def is_healthy(self):
            return True

    monkeypatch.setattr(run_demo, "create_datahub_client", lambda settings: Healthy())
    monkeypatch.setattr(
        run_demo,
        "_run_with_client",
        lambda *args, **kwargs: WritebackResult(status="INCOMPLETE", message="partial"),
    )

    assert run_demo.run_live() is False


def test_run_live_true_when_writeback_success(monkeypatch):
    class Healthy:
        def is_healthy(self):
            return True

    monkeypatch.setattr(run_demo, "create_datahub_client", lambda settings: Healthy())
    monkeypatch.setattr(
        run_demo,
        "_run_with_client",
        lambda *args, **kwargs: WritebackResult(status="SUCCESS", message="ok"),
    )

    assert run_demo.run_live() is True

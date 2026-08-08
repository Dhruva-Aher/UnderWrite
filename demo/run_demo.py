"""Judge-facing demo orchestrator.

Default path: live DataHub GMS → lineage traversal → policy verdict → writeback.
Offline fixtures exist only for reproducibility when GMS is unavailable.
"""

from __future__ import annotations

import argparse
import logging
import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agent import Agent
from config import settings
from datahub_client import WritebackResult, create_datahub_client, process_verdict_writeback_event
from metadata.client import MockMetadataClient

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("demo")

MODEL_URN = "urn:li:mlModel:(urn:li:dataPlatform:mlflow,churn_model_v2,PROD)"
OFFLINE_FIXTURE = "demo/fixtures/target_leakage_metadata.json"


def _print_verdict(agent: Agent, verdict) -> None:
    print(f"\nDiscovered {len(agent.last_graph.nodes)} assets via Lineage.")
    print(f"Policies Evaluated: {verdict.policies_evaluated}")
    print(f"Verdict: {verdict.verdict.value.upper()}")
    print(f"Reason Code: {verdict.reason_code}")

    if verdict.verdict.value == "blocked" and verdict.evidence_paths:
        print("\n--- Evidence Paths ---")
        for i, ep in enumerate(verdict.evidence_paths, start=1):
            print(
                f"{i}. Policy {ep.policy_id} triggered on node {ep.tainted_urn} "
                f"(tagged '{ep.tag_found}')"
            )
            print(f"   Path: {' -> '.join(ep.path)}")
            if getattr(ep, "rationale", None):
                print(f"   Rationale: {ep.rationale}")
        print("----------------------")
    else:
        print("\nMerge Approved. No policy violations.")


def _run_with_client(client, *, mode_label: str, writeback_is_live: bool) -> WritebackResult:
    print(f"Mode: {mode_label}")
    print(f"\nEvaluating deployment for model: {MODEL_URN}")

    agent = Agent(client=client, settings=settings)
    verdict = agent.evaluate_model(MODEL_URN)
    _print_verdict(agent, verdict)

    print("\nInitiating write-back...")
    if writeback_is_live:
        print("Target: LIVE DataHub GMS (incident/tag/documentation side effects)")
    else:
        print("Target: in-memory mock only (offline reproducibility — NOT live DataHub)")

    wb_result = process_verdict_writeback_event(
        verdict_data={
            "model_urn": MODEL_URN,
            "reason_code": verdict.reason_code,
            "verdict": verdict.verdict.value,
            "evidence_paths": verdict.evidence_paths,
        },
        client=client,
        gms_url=settings.gms_url if writeback_is_live else None,
    )
    scope = "live GMS" if writeback_is_live else "mock only (not GMS)"
    print(f"Writeback Status ({scope}): {wb_result.status} - {wb_result.message}")
    print("\nDemo Execution Complete.")
    return wb_result


def run_live() -> bool:
    """Return True only if live GMS evaluation and writeback both succeeded."""
    print("==============================================")
    print("   LIVE DataHub: metadata → gate → writeback")
    print("==============================================\n")
    print(f"Connecting to DataHub GMS at {settings.gms_url}...")

    try:
        client = create_datahub_client(settings)
        if not client.is_healthy():
            print(f"DataHub GMS unhealthy at {settings.gms_url}")
            return False
        print("DataHub GMS connected")
    except Exception as e:
        print(f"Failed to connect to DataHub GMS: {e}")
        return False

    wb_result = _run_with_client(
        client,
        mode_label="LIVE DataHub (authorization + writeback against GMS)",
        writeback_is_live=True,
    )
    if wb_result.status != "SUCCESS":
        print(f"Live path incomplete: writeback status={wb_result.status}")
        return False
    return True


def run_offline() -> None:
    print("==============================================")
    print("   OFFLINE fixture (reproducibility only)")
    print("==============================================\n")
    print(
        "This path does NOT talk to DataHub. Use it for CI/unit demos.\n"
        "Judges: prefer `python demo/run_demo.py` with GMS running "
        "(see README Quick Start).\n"
    )

    try:
        client = MockMetadataClient.load_fixture(OFFLINE_FIXTURE)
        print(f"Loaded offline fixture: {OFFLINE_FIXTURE}")
    except Exception as e:
        print(f"Failed to load fixture: {e}")
        sys.exit(1)

    _run_with_client(
        client,
        mode_label="OFFLINE mock fixture (not live DataHub)",
        writeback_is_live=False,
    )


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Underwrite demo: live DataHub by default; --offline for fixtures."
    )
    parser.add_argument(
        "--offline",
        action="store_true",
        help="Force offline fixture path (no DataHub GMS required).",
    )
    args = parser.parse_args()

    if args.offline:
        run_offline()
        return

    # Probe GMS once so a writeback failure after a live eval does not fall back
    # to the offline fixture (which would obscure the live result).
    gms_available = False
    try:
        gms_available = create_datahub_client(settings).is_healthy()
    except Exception:
        gms_available = False

    if run_live():
        return

    if gms_available:
        print(
            "\nLive GMS was reachable but the live path did not fully succeed "
            "(e.g. writeback incomplete). Not falling back to offline.\n"
        )
        sys.exit(1)

    print(
        "\nLive DataHub unavailable. Falling back to offline fixture.\n"
        "To force offline: python demo/run_demo.py --offline\n"
        "To run live: start DataHub GMS, seed with `python seed.py`, then re-run.\n"
    )
    run_offline()


if __name__ == "__main__":
    main()

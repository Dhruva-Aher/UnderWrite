"""Underwrite — Master Verification Suite (test_full_suite.py)."""

import json
import logging
import os
import subprocess
import sys

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger("underwrite.full_suite")

BASE_DIR = os.path.dirname(__file__)


def verify_fallback_layer() -> None:
    """Verify Layer 0 offline fallback fixtures."""
    logger.info("Testing Layer 0 Offline Fallback Fixtures...")
    cache_path = os.path.join(BASE_DIR, "cache", "verdicts.json")
    assert os.path.exists(cache_path), "cache/verdicts.json missing!"

    with open(cache_path) as f:
        data = json.load(f)

    m1 = "urn:li:mlModel:(urn:li:dataPlatform:mlflow,churn_model_v2,PROD)"
    m2 = "urn:li:mlModel:(urn:li:dataPlatform:mlflow,recommendation_model_v1,PROD)"
    m3 = "urn:li:mlModel:(urn:li:dataPlatform:mlflow,fraud_model_v3,PROD)"

    assert m1 in data and data[m1]["verdict"] == "blocked"
    assert m2 in data and data[m2]["verdict"] == "approved"
    assert m3 in data and data[m3]["verdict"] == "blocked"

    for urn, val in data.items():
        graph = val.get("graph")
        assert graph is not None, f"Missing graph layout for {urn}"
        assert len(graph["nodes"]) > 0
        assert len(graph["edges"]) > 0

    logger.info("Layer 0 Offline Fallback Fixtures PASSED")


def run_pytest(target_dir: str) -> bool:
    """Run pytest on specified directory."""
    logger.info("Running pytest %s...", target_dir)
    res = subprocess.run(
        [sys.executable, "-m", "pytest", target_dir],
        capture_output=True,
        text=True,
        check=False,
    )
    if res.returncode == 0:
        logger.info("pytest %s PASSED", target_dir)
        return True
    else:
        logger.error("pytest %s FAILED:\n%s\n%s", target_dir, res.stderr, res.stdout)
        return False


def main() -> None:
    """Execute full master verification suite."""
    print("==================================================")
    print("   UNDERWRITE MASTER VERIFICATION TEST SUITE      ")
    print("==================================================\n")

    verify_fallback_layer()
    assert run_pytest("tests/unit"), "Unit tests failed"
    assert run_pytest("tests/integration"), "Integration tests failed"

    print("\n==================================================")
    print("MASTER SUITE SUCCESS: configured checks passed.")
    print("==================================================")


if __name__ == "__main__":
    main()

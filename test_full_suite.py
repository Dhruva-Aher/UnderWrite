"""Underwrite — Master Verification Suite (test_full_suite.py)."""

import logging
import subprocess
import sys

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger("underwrite.full_suite")


def run_pytest(target_dir: str, allow_all_skipped: bool = False) -> bool:
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
    # pytest returns 5 when collection contains no runnable tests.  Live
    # integration modules intentionally skip at collection time when no GMS is
    # configured; that is an expected offline verification state, not a test
    # failure.  Do not apply this exception to the unit suite.
    if allow_all_skipped and res.returncode == 5 and "skipped" in res.stdout:
        logger.warning(
            "pytest %s has no runnable tests because live GMS is unavailable; "
            "integration verification was skipped",
            target_dir,
        )
        return True
    else:
        logger.error("pytest %s FAILED:\n%s\n%s", target_dir, res.stderr, res.stdout)
        return False


def main() -> None:
    """Execute full master verification suite."""
    print("==================================================")
    print("   UNDERWRITE MASTER VERIFICATION TEST SUITE      ")
    print("==================================================\n")

    assert run_pytest("tests/unit"), "Unit tests failed"
    assert run_pytest("tests/integration", allow_all_skipped=True), "Integration tests failed"

    print("\n==================================================")
    print("MASTER SUITE SUCCESS: configured checks passed.")
    print("==================================================")


if __name__ == "__main__":
    main()

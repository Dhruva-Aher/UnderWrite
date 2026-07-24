"""Underwrite — Demo Preflight Check & Server Launcher (preflight.py)

Ensures zero demo failures:
1. Refuses to start when the configured server port is already occupied.
2. Checks DataHub GMS status.
3. Verifies cache fixtures (cache/verdicts.json).
4. Runs unit test suite (`pytest tests/unit`).
5. Boots FastAPI application using config settings.
"""

import logging
import os
import subprocess
import sys
import time

import httpx

from config import settings

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger("underwrite.preflight")


def check_port_available(port: int = settings.port) -> bool:
    """Check for a port conflict without terminating another process."""
    logger.info("Checking for existing processes on port %d...", port)
    try:
        res = subprocess.run(
            ["lsof", "-t", f"-i:{port}"], capture_output=True, text=True, check=False
        )
        if res.stdout.strip():
            pids = res.stdout.strip().split("\n")
            logger.error(
                "Port %d is already in use by process(es): %s. Stop the intended "
                "server or set UNDERWRITE_PORT before running preflight.",
                port,
                pids,
            )
            return False
        else:
            logger.info("Port %d is clear", port)
            return True
    except (subprocess.SubprocessError, OSError) as e:
        logger.warning("Port check warning: %s", e)
        return False


def verify_cache_fixtures() -> None:
    """Verify Layer 0 offline cache fixture file."""
    logger.info("Verifying cache fixtures...")
    cache_path = os.path.join(os.path.dirname(__file__), "cache", "verdicts.json")
    if os.path.exists(cache_path):
        logger.info("Layer 0 fixture found (%s)", cache_path)
    else:
        logger.error("CRITICAL: cache/verdicts.json missing!")
        sys.exit(1)


def check_datahub_gms() -> bool:
    """Check if local DataHub GMS container is reachable."""
    logger.info("Checking DataHub GMS status...")
    try:
        r = httpx.get(f"{settings.gms_url}/healthcheck", timeout=3.0)
        if r.status_code == 200:
            logger.info("DataHub GMS is ONLINE at %s", settings.gms_url)
            return True
    except httpx.HTTPError as e:
        logger.warning("DataHub GMS health check failed (%s)", e)
    logger.warning(
        "DataHub GMS is OFFLINE — system will operate in Layer 0 cached fallback mode"
    )
    return False


def run_tests() -> None:
    """Run detection unit test suite."""
    logger.info("Running detection engine unit test suite...")
    res = subprocess.run(
        [sys.executable, "-m", "pytest", "tests/unit"],
        capture_output=True,
        text=True,
        check=False,
    )
    if res.returncode == 0:
        logger.info("Detection engine unit tests PASSED")
    else:
        logger.error("Detection unit tests failed:\n%s", res.stderr)
        sys.exit(1)


def launch_server() -> None:
    """Launch FastAPI uvicorn server with config settings."""
    logger.info("Launching Underwrite application server...")
    print("\n==================================================")
    print("🚀 Underwrite is READY for Live Demo!")
    print(f"   URL: http://{settings.host}:{settings.port}")
    print("==================================================\n")
    subprocess.run(
        [
            sys.executable,
            "-m",
            "uvicorn",
            "app:app",
            "--host",
            settings.host,
            "--port",
            str(settings.port),
        ],
        check=False,
    )


def main():
    """Run preflight sequence."""
    print("==================================================")
    print("      UNDERWRITE DEMO PREFLIGHT VERIFICATION      ")
    print("==================================================")
    if not check_port_available(settings.port):
        sys.exit(1)
    verify_cache_fixtures()
    check_datahub_gms()
    run_tests()
    launch_server()


if __name__ == "__main__":
    main()

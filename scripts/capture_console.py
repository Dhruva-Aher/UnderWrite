"""Drive the live console with a real browser, assert it is clean, and capture docs screenshots.

Doubles as the UI regression check: any console error, page error, or failed
request fails the run, so a screenshot can never be captured from a broken page.

    python scripts/capture_console.py [--base-url http://127.0.0.1:8000]
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

REPO_ROOT = Path(__file__).resolve().parent.parent
SHOTS = REPO_ROOT / "docs" / "screenshots"

BLOCKED = "urn:li:mlModel:(urn:li:dataPlatform:mlflow,churn_model_v2,PROD)"
APPROVED = "urn:li:mlModel:(urn:li:dataPlatform:mlflow,recommendation_model_v1,PROD)"


def run_evaluation(page, base_url: str, model_urn: str) -> None:
    page.goto(base_url, wait_until="networkidle")
    page.fill('input[type="text"]', model_urn)
    page.get_by_role("button", name="Evaluate", exact=False).first.click()
    # The verdict headline only leaves NOT EVALUATED once /evaluate resolves.
    page.wait_for_function(
        "() => !document.body.innerText.includes('NOT EVALUATED')", timeout=30_000
    )
    page.wait_for_timeout(1_000)


def shoot(page, name: str) -> None:
    SHOTS.mkdir(parents=True, exist_ok=True)
    page.screenshot(path=str(SHOTS / name), full_page=True)
    print(f"  captured {name}")


def section(page, index: str, name: str) -> None:
    node = page.locator(f"section:has-text('{index}')").first
    if node.count():
        SHOTS.mkdir(parents=True, exist_ok=True)
        node.screenshot(path=str(SHOTS / name))
        print(f"  captured {name}")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-url", default="http://127.0.0.1:8000")
    args = parser.parse_args()

    problems: list[str] = []

    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 1440, "height": 1000})

        page.on("pageerror", lambda e: problems.append(f"pageerror: {e}"))
        page.on(
            "console",
            lambda m: problems.append(f"console.{m.type}: {m.text}")
            if m.type in ("error", "warning")
            else None,
        )
        page.on(
            "requestfailed",
            lambda r: problems.append(f"requestfailed: {r.url} {r.failure}"),
        )

        print("blocked path:")
        run_evaluation(page, args.base_url, BLOCKED)
        blocked_text = page.inner_text("body")
        shoot(page, "01-blocked-decision.png")
        section(page, "03", "02-blocked-evidence.png")
        section(page, "04", "03-lineage-graph.png")
        # Write-back is a background task; wait for the polled status to settle.
        page.wait_for_timeout(4_000)
        section(page, "05", "04-writeback.png")

        print("approved path:")
        run_evaluation(page, args.base_url, APPROVED)
        approved_text = page.inner_text("body")
        shoot(page, "05-approved-decision.png")

        browser.close()

    for label, text, expected in (
        ("blocked", blocked_text, "BLOCKED"),
        ("approved", approved_text, "APPROVED"),
    ):
        if expected not in text:
            problems.append(f"{label} run never rendered {expected}")
        if "(None)" in text or "undefined" in text:
            problems.append(f"{label} run rendered a placeholder value")

    if "No evidence yet" in approved_text:
        problems.append("approved run showed the idle 'No evidence yet' copy")
    if "urn:li:corpuser:unknown" in blocked_text:
        problems.append("blocked run showed an anonymous principal")

    if problems:
        print("\nFAILED:")
        for problem in problems:
            print(f"  - {problem}")
        return 1

    print("\nConsole clean: no page errors, no console errors/warnings, no failed requests.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

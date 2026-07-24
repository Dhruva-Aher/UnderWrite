"""
Underwrite — Marketing Screenshot Generator
Captures 7 publication-quality screenshot assets for Devpost, GitHub README, and Slides.
"""

import os
import time
from pathlib import Path
from playwright.sync_api import sync_playwright

OUTPUT_DIR = Path(__file__).parent / "screenshots"
OUTPUT_DIR.mkdir(exist_ok=True)

URL = os.getenv("UNDERWRITE_SCREENSHOT_URL", "http://127.0.0.1:8000")
VIEWPORT = {"width": 1440, "height": 900}


def capture_all():
    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,
            args=["--no-sandbox", "--disable-setuid-sandbox"],
        )
        context = browser.new_context(
            viewport=VIEWPORT,
            device_scale_factor=2,  # 2x Retina crisp resolution
            color_scheme="dark",
        )
        page = context.new_page()

        # 1. Hero (Clean landing page)
        print("1. Capturing 01-hero.png...")
        page.goto(URL)
        page.wait_for_selector(".app-header")
        time.sleep(0.6)
        page.screenshot(path=OUTPUT_DIR / "01-hero.png")

        # 2. Blocked Deployment (churn_model_v2 evaluated)
        print("2. Capturing 02-blocked.png...")
        page.click("#evaluate-btn")
        page.wait_for_selector("#verdict-section.is-visible")
        time.sleep(0.8)
        page.screenshot(path=OUTPUT_DIR / "02-blocked.png")

        # 3. Interactive Lineage
        print("3. Capturing 03-lineage.png...")
        # Blocked verdicts automatically open the graph panel.
        node = page.query_selector("[data-id='raw_billing']")
        if node and node.is_visible():
            node.click()
            time.sleep(0.5)
        page.screenshot(path=OUTPUT_DIR / "03-lineage.png")
        page.click("#trigger-graph")  # Close graph panel
        time.sleep(0.4)

        # 4. Execution Pipeline
        print("4. Capturing 04-replay.png...")
        page.click("#trigger-pipeline")
        time.sleep(0.6)
        page.screenshot(path=OUTPUT_DIR / "04-replay.png")
        page.click("#trigger-pipeline")  # Close pipeline panel
        time.sleep(0.4)

        # 5. DataHub Write-Back
        print("5. Capturing 05-writeback.png...")
        page.click("#trigger-writeback")
        time.sleep(0.6)
        page.screenshot(path=OUTPUT_DIR / "05-writeback.png")

        # 6. Approved Deployment (churn_model_v2_fixed evaluated)
        print("6. Capturing 06-approved.png...")
        page.goto(URL)
        page.wait_for_selector("#model-select")
        page.select_option(
            "#model-select",
            "urn:li:mlModel:(urn:li:dataPlatform:mlflow,churn_model_v2_fixed,PROD)",
        )
        page.click("#evaluate-btn")
        page.wait_for_selector("#verdict-section.is-visible")
        time.sleep(0.8)
        page.screenshot(path=OUTPUT_DIR / "06-approved.png")

        # 7. Offline Mode
        print("7. Capturing 07-offline.png...")
        page.goto(URL)
        page.wait_for_selector("#status-indicator")
        time.sleep(0.6)
        page.screenshot(path=OUTPUT_DIR / "07-offline.png")

        browser.close()
        print("🎉 All 7 screenshots captured successfully!")


if __name__ == "__main__":
    capture_all()

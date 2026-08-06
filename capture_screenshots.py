import os
import time
from pathlib import Path
from playwright.sync_api import sync_playwright

OUTPUT_DIR = Path(__file__).parent / "screenshots"
OUTPUT_DIR.mkdir(exist_ok=True)

URL = os.getenv("UNDERWRITE_SCREENSHOT_URL", "http://127.0.0.1:8002")
VIEWPORT = {"width": 1440, "height": 1000}


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
        page.on("console", lambda msg: print(f"BROWSER_CONSOLE: {msg.text}"))
        page.on("pageerror", lambda err: print(f"BROWSER_ERROR: {err}"))

        print(f"Loading {URL}...")
        page.goto(URL)
        page.wait_for_selector("text=Trust Evaluation Request")
        time.sleep(2)  # Wait for React to render and fonts to load

        # 1. Hero (Clean landing page)
        print("1. Capturing 01-hero.png...")
        page.screenshot(path=OUTPUT_DIR / "01-hero.png", full_page=True)

        # 2. Blocked Deployment (02 Trust Decision)
        print("2. Capturing 02-blocked.png...")
        page.locator('section[aria-labelledby="sec-02"]').screenshot(path=OUTPUT_DIR / "02-blocked.png")

        # 3. Interactive Lineage (04 FineGrainedLineage)
        print("3. Capturing 03-lineage.png...")
        page.locator('section[aria-labelledby="sec-04"]').screenshot(path=OUTPUT_DIR / "03-lineage.png")

        # 4. Execution Pipeline (06 Trust Trace)
        print("4. Capturing 04-replay.png...")
        page.locator('section[aria-labelledby="sec-06"]').screenshot(path=OUTPUT_DIR / "04-replay.png")

        # 5. DataHub Write-Back (05 Metadata Mutation)
        print("5. Capturing 05-writeback.png...")
        page.locator('section[aria-labelledby="sec-05"]').screenshot(path=OUTPUT_DIR / "05-writeback.png")

        # 6. Approved Deployment (03 Trust Proof)
        print("6. Capturing 06-approved.png...")
        page.locator('section[aria-labelledby="sec-03"]').screenshot(path=OUTPUT_DIR / "06-approved.png")

        # 7. Offline Mode (01 Trust Evaluation Request)
        print("7. Capturing 07-offline.png...")
        page.locator('section[aria-labelledby="sec-01"]').screenshot(path=OUTPUT_DIR / "07-offline.png")

        browser.close()
        print("🎉 All 7 screenshots captured successfully!")


if __name__ == "__main__":
    capture_all()

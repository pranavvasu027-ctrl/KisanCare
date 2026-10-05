"""
Script to capture headless browser screenshots of the running Streamlit UI (Phase 5, Section 23).
"""

from pathlib import Path
import subprocess
import time

ROOT_DIR = Path(__file__).resolve().parent.parent
SCREENSHOT_DIR = ROOT_DIR / "reports" / "screenshots"
SCREENSHOT_DIR.mkdir(parents=True, exist_ok=True)

CHROME_PATH = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
BASE_URL = "http://localhost:8501"

TARGETS = [
    ("A_main_input_page.png", f"{BASE_URL}", 1280, 1100),
    ("B_disease_prediction.png", f"{BASE_URL}/?preset=tomato_eb", 1280, 3000),
    ("C_treatment_recommendation.png", f"{BASE_URL}/?preset=apple_scab", 1280, 3000),
    ("D_warning_provenance_mismatch.png", f"{BASE_URL}/?preset=mismatch", 1280, 2600),
    ("E_pest_detection.png", f"{BASE_URL}/?preset=corn_rust", 1280, 3000),
]


def capture():
    print(f"Capturing UI screenshots to {SCREENSHOT_DIR}...")
    for filename, url, width, height in TARGETS:
        out_file = SCREENSHOT_DIR / filename
        cmd = [
            CHROME_PATH,
            "--headless=new",
            f"--screenshot={str(out_file)}",
            f"--window-size={width},{height}",
            "--virtual-time-budget=7000",
            "--hide-scrollbars",
            url,
        ]
        print(f"Capturing {filename} ({width}x{height}) from {url}...")
        try:
            res = subprocess.run(cmd, capture_output=True, timeout=40)
            if out_file.exists():
                print(f"  [OK] Saved {filename} ({out_file.stat().st_size} bytes)")
            else:
                print(f"  [FAIL] Failed to create {filename}: {res.stderr.decode('utf-8', errors='ignore')}")
        except Exception as e:
            print(f"  [ERROR] Error capturing {filename}: {e}")
        time.sleep(2)


if __name__ == "__main__":
    capture()

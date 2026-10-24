"""Package the disease_pest_ai project into a new folder named 'diseasemodel'

and generate a clean zip archive including the API key configuration.
"""

import os
from pathlib import Path
import shutil
import zipfile

SRC_DIR = Path(__file__).resolve().parent.parent
DEST_DIR = SRC_DIR.parent / "diseasemodel"
ZIP_PATH_INSIDE = DEST_DIR / "diseasemodel.zip"
ZIP_PATH_PARENT = SRC_DIR.parent / "diseasemodel.zip"

EXCLUDE_DIRS = {"__pycache__", ".pytest_cache", ".git", ".idea", ".vscode"}
EXCLUDE_EXTS = {".pyc", ".pyo"}


def package():
    print(f"Packaging from: {SRC_DIR}")
    print(f"Target folder:  {DEST_DIR}")

    # Ensure destination directory exists
    DEST_DIR.mkdir(parents=True, exist_ok=True)

    # 1. Copy files to diseasemodel directory
    copied_count = 0
    for root, dirs, files in os.walk(SRC_DIR):
        dirs[:] = [d for d in dirs if d not in EXCLUDE_DIRS and d != "diseasemodel"]
        rel_root = Path(root).relative_to(SRC_DIR)
        target_root = DEST_DIR / rel_root
        target_root.mkdir(parents=True, exist_ok=True)

        for f in files:
            if any(f.endswith(ext) for ext in EXCLUDE_EXTS):
                continue
            if f == "diseasemodel.zip":
                continue

            src_file = Path(root) / f
            dest_file = target_root / f
            shutil.copy2(src_file, dest_file)
            copied_count += 1

    print(f"Successfully copied {copied_count} files into {DEST_DIR}")

    # Verify .env exists in target
    dest_env = DEST_DIR / ".env"
    if dest_env.exists():
        print(f"Verified .env exists in target folder ({dest_env.stat().st_size} bytes)")
    else:
        print("WARNING: .env not found in target folder!")

    # 2. Create ZIP archive
    print(f"Creating zip archive at {ZIP_PATH_PARENT}...")
    with zipfile.ZipFile(ZIP_PATH_PARENT, "w", zipfile.ZIP_DEFLATED) as zf:
        for root, dirs, files in os.walk(DEST_DIR):
            dirs[:] = [d for d in dirs if d not in EXCLUDE_DIRS]
            for f in files:
                if f.endswith(".zip") or any(f.endswith(ext) for ext in EXCLUDE_EXTS):
                    continue
                file_path = Path(root) / f
                arcname = file_path.relative_to(DEST_DIR)
                zf.write(file_path, arcname)

    # Also copy zip inside DEST_DIR for convenience
    shutil.copy2(ZIP_PATH_PARENT, ZIP_PATH_INSIDE)

    print(f"Zip created: {ZIP_PATH_PARENT} ({ZIP_PATH_PARENT.stat().st_size / (1024*1024):.2f} MB)")
    print(f"Zip copy created: {ZIP_PATH_INSIDE} ({ZIP_PATH_INSIDE.stat().st_size / (1024*1024):.2f} MB)")

    # 3. Verify ZIP contents
    with zipfile.ZipFile(ZIP_PATH_PARENT, "r") as zf:
        namelist = zf.namelist()
        has_env = ".env" in namelist
        has_api = any("api/main.py" in name for name in namelist)
        has_pipeline = any("inference/pipeline.py" in name for name in namelist)
        print(f"Zip verification: total items = {len(namelist)}")
        print(f"  Contains .env with API key: {has_env}")
        print(f"  Contains FastAPI main.py:   {has_api}")
        print(f"  Contains ML pipeline:       {has_pipeline}")


if __name__ == "__main__":
    package()

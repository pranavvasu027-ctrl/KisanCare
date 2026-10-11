"""Tests ensuring strict exclusion of Disease/Pest model from the inference backend."""

import os
import sys
from fastapi.testclient import TestClient

from api.main import app

client = TestClient(app)


def test_no_disease_pest_routes_exist():
    """Verify no disease or pest endpoints are exposed in the FastAPI application."""
    routes = [route.path for route in app.routes if hasattr(route, "path")]

    for r in routes:
        assert "/disease" not in r, f"Forbidden route exposed: {r}"
        assert "/pest" not in r, f"Forbidden route exposed: {r}"

    # Also test querying those forbidden endpoints returns 404
    r1 = client.get("/disease")
    assert r1.status_code == 404

    r2 = client.post("/api/disease/predict", json={})
    assert r2.status_code == 404

    r3 = client.get("/pest")
    assert r3.status_code == 404


def test_no_disease_pest_modules_imported():
    """Verify that neither disease_pest_ai nor any disease model module is loaded in sys.modules."""
    forbidden_modules = [
        mod for mod in sys.modules
        if ("disease" in mod.lower() or "pest" in mod.lower())
        and not mod.startswith("tests")
        and not mod.startswith("pytest")
    ]
    # Check for domain modules
    domain_forbidden = [m for m in forbidden_modules if "disease_pest" in m or "disease" in m or "pest" in m]
    assert len(domain_forbidden) == 0, f"Disease/pest modules found in sys.modules: {domain_forbidden}"


def test_no_disease_pest_files_in_backend_or_models():
    """Verify no disease/pest code or weights are located within api/ or models/."""
    current_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    scan_dirs = [os.path.join(current_dir, "api"), os.path.join(current_dir, "models")]

    found_forbidden_files = []
    for d in scan_dirs:
        for root, dirs, files in os.walk(d):
            for f in files:
                lower_f = f.lower()
                if "disease" in lower_f or "pest" in lower_f:
                    found_forbidden_files.append(os.path.join(root, f))

    assert len(found_forbidden_files) == 0, f"Forbidden files discovered: {found_forbidden_files}"

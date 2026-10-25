"""
Comprehensive Test Suite for Strict Plant Leaf Image Validation Gate.
Tests both the PlantLeafValidator unit logic and the FastAPI /api/v1/disease-detection endpoint.
"""

import io
import os
import sys
from pathlib import Path
import numpy as np
import pytest
from fastapi.testclient import TestClient
from PIL import Image, ImageDraw

# Ensure paths
REPO_ROOT = Path(__file__).resolve().parent.parent
SERVICES_DIR = REPO_ROOT / "services"
if str(SERVICES_DIR) not in sys.path:
    sys.path.insert(0, str(SERVICES_DIR))
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from backend.app.main import app
from disease_pest_ai.inference.validator import PlantLeafValidator, get_plant_validator

client = TestClient(app)

TEST_DATA_DIR = SERVICES_DIR / "disease_pest_ai" / "test_data"


def make_synthetic_image(category: str) -> Image.Image:
    """Creates textured synthetic test images of various invalid categories."""
    if category == "laptop":
        img = Image.new("RGB", (320, 320), color=(180, 170, 160))
        d = ImageDraw.Draw(img)
        d.rectangle([40, 30, 280, 190], fill=(20, 20, 25), outline=(100, 100, 100), width=4)
        d.rectangle([55, 45, 265, 175], fill=(30, 70, 120))
        d.text((70, 70), "Windows 11 Desktop\nVisual Studio Code\nTerminal", fill=(255, 255, 255))
        d.polygon([(20, 290), (300, 290), (280, 190), (40, 190)], fill=(190, 190, 195))
        for y in range(200, 260, 12):
            for x in range(50, 270, 18):
                d.rectangle([x, y, x + 14, y + 9], fill=(40, 40, 40))
        d.rectangle([120, 265, 200, 285], fill=(160, 160, 165))
    elif category == "mobile_phone":
        img = Image.new("RGB", (320, 320), color=(200, 200, 200))
        d = ImageDraw.Draw(img)
        d.rectangle([90, 30, 230, 290], fill=(20, 20, 20), outline=(50, 50, 50), width=5)
        d.rectangle([100, 50, 220, 270], fill=(240, 240, 250))
        d.text((110, 80), "Messages\n9:41 AM\nNotifications", fill=(10, 10, 10))
    elif category == "person":
        img = Image.new("RGB", (320, 320), color=(100, 140, 180))
        d = ImageDraw.Draw(img)
        d.ellipse([100, 50, 220, 190], fill=(235, 185, 145))
        d.rectangle([60, 180, 260, 320], fill=(40, 50, 120))
        d.ellipse([125, 100, 145, 115], fill=(50, 40, 30))
        d.ellipse([175, 100, 195, 115], fill=(50, 40, 30))
        d.line([(140, 160), (180, 160)], fill=(160, 60, 60), width=3)
    elif category == "building":
        img = Image.new("RGB", (320, 320), color=(120, 180, 230))
        d = ImageDraw.Draw(img)
        d.rectangle([40, 80, 280, 320], fill=(160, 150, 140), outline=(60, 60, 60), width=2)
        for by in range(100, 300, 35):
            for bx in range(60, 260, 35):
                d.rectangle([bx, by, bx + 22, by + 25], fill=(220, 230, 240), outline=(80, 80, 80))
    elif category == "vehicle":
        img = Image.new("RGB", (320, 320), color=(170, 180, 175))
        d = ImageDraw.Draw(img)
        d.rectangle([20, 250, 300, 320], fill=(60, 60, 60))
        d.polygon([(60, 160), (110, 100), (220, 100), (270, 160)], fill=(50, 120, 200))
        d.rectangle([30, 160, 290, 230], fill=(200, 30, 30))
        d.ellipse([60, 200, 120, 260], fill=(20, 20, 20))
        d.ellipse([200, 200, 260, 260], fill=(20, 20, 20))
    elif category == "animal":
        img = Image.new("RGB", (320, 320), color=(160, 170, 160))
        d = ImageDraw.Draw(img)
        d.ellipse([80, 100, 240, 220], fill=(160, 110, 60))  # body
        d.ellipse([60, 60, 140, 140], fill=(160, 110, 60))  # head
        d.polygon([(65, 60), (85, 20), (105, 60)], fill=(120, 70, 30))  # ear
        d.polygon([(100, 60), (120, 20), (140, 60)], fill=(120, 70, 30))  # ear
        d.ellipse([75, 80, 90, 95], fill=(20, 20, 20))  # eye
        d.ellipse([50, 90, 75, 115], fill=(20, 20, 20))  # snout
    elif category == "screenshot":
        img = Image.new("RGB", (320, 320), color=(245, 245, 245))
        d = ImageDraw.Draw(img)
        d.rectangle([10, 10, 310, 40], fill=(40, 100, 200))
        d.text((20, 18), "Accounting Software v2.4 - Invoice Summary", fill=(255, 255, 255))
        for y in range(60, 280, 20):
            d.line([(30, y), (290, y)], fill=(180, 180, 180), width=2)
            d.text((30, y - 12), f"Ledger Transaction {y}: Debit 5,000 INR", fill=(30, 30, 30))
    elif category == "blank":
        return Image.new("RGB", (320, 320), color=(255, 255, 255))
    elif category == "dark":
        return Image.new("RGB", (320, 320), color=(5, 5, 5))
    elif category == "blurry":
        # Ultra blurred image
        base = Image.open(TEST_DATA_DIR / "tomato_healthy.jpg")
        return base.resize((4, 4)).resize((320, 320), Image.Resampling.BILINEAR)
    else:
        img = Image.new("RGB", (320, 320), color=(150, 150, 150))

    # Add realistic photographic noise so Laplacian variance passes quality gate
    arr = np.array(img).astype(np.float32)
    noise = np.random.normal(0, 12, arr.shape)
    arr = np.clip(arr + noise, 0, 255).astype(np.uint8)
    return Image.fromarray(arr)


def img_to_bytes(img: Image.Image) -> io.BytesIO:
    """Converts PIL image to JPEG BytesIO."""
    buf = io.BytesIO()
    img.save(buf, format="JPEG")
    buf.seek(0)
    return buf


# =============================================================================
# UNIT TESTS: PlantLeafValidator
# =============================================================================

class TestPlantLeafValidator:
    """Unit tests for PlantLeafValidator."""

    @pytest.fixture(scope="class")
    def validator(self):
        return get_plant_validator()

    def test_valid_tomato_early_blight_passes(self, validator):
        img = Image.open(TEST_DATA_DIR / "tomato_early_blight.jpg")
        res = validator.validate(img)
        assert res.is_valid_plant_image is True
        assert res.plant_confidence >= 0.70
        assert res.leaf_confidence >= 0.70
        assert res.status == "VALID"
        assert res.reason == "VALID"

    def test_valid_tomato_healthy_passes(self, validator):
        img = Image.open(TEST_DATA_DIR / "tomato_healthy.jpg")
        res = validator.validate(img)
        assert res.is_valid_plant_image is True
        assert res.plant_confidence >= 0.70
        assert res.leaf_confidence >= 0.70
        assert res.status == "VALID"

    def test_valid_corn_rust_passes(self, validator):
        img = Image.open(TEST_DATA_DIR / "corn_common_rust.jpg")
        res = validator.validate(img)
        assert res.is_valid_plant_image is True
        assert res.plant_confidence >= 0.70
        assert res.leaf_confidence >= 0.70

    def test_valid_apple_scab_passes(self, validator):
        img = Image.open(TEST_DATA_DIR / "apple_scab_bierny.jpg")
        res = validator.validate(img)
        assert res.is_valid_plant_image is True
        assert res.plant_confidence >= 0.70
        assert res.leaf_confidence >= 0.70

    @pytest.mark.parametrize("invalid_category", [
        "laptop",
        "mobile_phone",
        "person",
        "building",
        "vehicle",
        "animal",
        "screenshot",
        "blank",
        "dark",
        "blurry",
    ])
    def test_invalid_categories_rejected(self, validator, invalid_category):
        img = make_synthetic_image(invalid_category)
        res = validator.validate(img)
        assert res.is_valid_plant_image is False
        assert res.status == "INVALID_IMAGE"
        assert res.reason in [
            "NO_PLANT_DETECTED",
            "NO_LEAF_DETECTED",
            "IMAGE_TOO_BLURRY",
            "IMAGE_TOO_DARK",
            "LOW_IMAGE_QUALITY",
            "UNRELATED_IMAGE",
        ]
        assert "Invalid photo" in res.message or "blur" in res.message.lower() or "dark" in res.message.lower() or "blank" in res.message.lower()


# =============================================================================
# ENDPOINT TESTS: FastAPI POST /api/v1/disease-detection
# =============================================================================

class TestDiseaseDetectionEndpoint:
    """End-to-end endpoint tests for /api/v1/disease-detection."""

    def test_endpoint_valid_leaf_upload_returns_valid_diagnosis(self):
        """Valid leaf image must pass validation and return full disease result."""
        img = Image.open(TEST_DATA_DIR / "tomato_early_blight.jpg")
        buf = img_to_bytes(img)

        resp = client.post(
            "/api/v1/disease-detection",
            data={"crop": "Tomato"},
            files={"file": ("leaf.jpg", buf, "image/jpeg")},
        )
        assert resp.status_code == 200
        body = resp.json()

        # Contract assertion
        assert body["success"] is True
        assert body["status"] == "VALID"
        assert body["is_valid_plant_image"] is True
        assert body["plant_confidence"] >= 0.70
        assert body["leaf_confidence"] >= 0.70
        assert "disease" in body
        assert "Early Blight" in body["disease"]
        assert body["disease_confidence"] > 0.50
        assert body["severity"] in ["HIGH", "MEDIUM", "LOW"]

        # Ensure UI result data is populated
        data = body["data"]
        assert data["condition"] == body["disease"]
        assert data["confidence_percent"] > 50
        assert "treatments" in data

    def test_endpoint_rejects_laptop_image(self):
        """Laptop image must fail validation, return INVALID_IMAGE, and NEVER return disease."""
        laptop_img = make_synthetic_image("laptop")
        buf = img_to_bytes(laptop_img)

        resp = client.post(
            "/api/v1/disease-detection",
            data={"crop": "Tomato"},
            files={"file": ("laptop.jpg", buf, "image/jpeg")},
        )
        assert resp.status_code == 200
        body = resp.json()

        assert body["success"] is False
        assert body["status"] == "INVALID_IMAGE"
        assert body["is_valid_plant_image"] is False
        assert body["plant_confidence"] < 0.70
        assert "message" in body
        assert "reason" in body
        assert body["reason"] in ["UNRELATED_IMAGE", "NO_PLANT_DETECTED"]
        # CRITICAL: Must NEVER fabricate a disease!
        assert "disease" not in body
        assert "Unknown Foliar Condition" not in str(body)

    def test_endpoint_rejects_person_photo(self):
        """Person/face image must fail validation and return INVALID_IMAGE."""
        person_img = make_synthetic_image("person")
        buf = img_to_bytes(person_img)

        resp = client.post(
            "/api/v1/disease-detection",
            data={"crop": "Tomato"},
            files={"file": ("person.jpg", buf, "image/jpeg")},
        )
        assert resp.status_code == 200
        body = resp.json()

        assert body["success"] is False
        assert body["status"] == "INVALID_IMAGE"
        assert body["is_valid_plant_image"] is False
        assert "disease" not in body

    def test_endpoint_rejects_vehicle_photo(self):
        """Car/vehicle image must fail validation and return INVALID_IMAGE."""
        car_img = make_synthetic_image("vehicle")
        buf = img_to_bytes(car_img)

        resp = client.post(
            "/api/v1/disease-detection",
            data={"crop": "Cotton"},
            files={"file": ("car.jpg", buf, "image/jpeg")},
        )
        assert resp.status_code == 200
        body = resp.json()

        assert body["success"] is False
        assert body["status"] == "INVALID_IMAGE"
        assert body["is_valid_plant_image"] is False
        assert "disease" not in body

    def test_endpoint_rejects_building_photo(self):
        """Building image must fail validation and return INVALID_IMAGE."""
        bldg_img = make_synthetic_image("building")
        buf = img_to_bytes(bldg_img)

        resp = client.post(
            "/api/v1/disease-detection",
            data={"crop": "Apple"},
            files={"file": ("building.jpg", buf, "image/jpeg")},
        )
        assert resp.status_code == 200
        body = resp.json()

        assert body["success"] is False
        assert body["status"] == "INVALID_IMAGE"
        assert "disease" not in body

    def test_endpoint_rejects_screenshot_photo(self):
        """UI screenshot must fail validation and return INVALID_IMAGE."""
        ss_img = make_synthetic_image("screenshot")
        buf = img_to_bytes(ss_img)

        resp = client.post(
            "/api/v1/disease-detection",
            data={"crop": "Corn"},
            files={"file": ("screenshot.jpg", buf, "image/jpeg")},
        )
        assert resp.status_code == 200
        body = resp.json()

        assert body["success"] is False
        assert body["status"] == "INVALID_IMAGE"
        assert "disease" not in body

    def test_endpoint_rejects_blank_image(self):
        """Blank image must fail quality check and return LOW_IMAGE_QUALITY."""
        blank_img = make_synthetic_image("blank")
        buf = img_to_bytes(blank_img)

        resp = client.post(
            "/api/v1/disease-detection",
            data={"crop": "Tomato"},
            files={"file": ("blank.jpg", buf, "image/jpeg")},
        )
        assert resp.status_code == 200
        body = resp.json()

        assert body["success"] is False
        assert body["status"] == "INVALID_IMAGE"
        assert body["reason"] == "LOW_IMAGE_QUALITY"
        assert "disease" not in body

    def test_endpoint_rejects_dark_image(self):
        """Dark image must fail quality check and return IMAGE_TOO_DARK."""
        dark_img = make_synthetic_image("dark")
        buf = img_to_bytes(dark_img)

        resp = client.post(
            "/api/v1/disease-detection",
            data={"crop": "Tomato"},
            files={"file": ("dark.jpg", buf, "image/jpeg")},
        )
        assert resp.status_code == 200
        body = resp.json()

        assert body["success"] is False
        assert body["status"] == "INVALID_IMAGE"
        assert body["reason"] == "IMAGE_TOO_DARK"
        assert "disease" not in body

    def test_endpoint_rejects_blurry_image(self):
        """Extremely blurry image must fail quality check and return IMAGE_TOO_BLURRY."""
        blurry_img = make_synthetic_image("blurry")
        buf = img_to_bytes(blurry_img)

        resp = client.post(
            "/api/v1/disease-detection",
            data={"crop": "Tomato"},
            files={"file": ("blurry.jpg", buf, "image/jpeg")},
        )
        assert resp.status_code == 200
        body = resp.json()

        assert body["success"] is False
        assert body["status"] == "INVALID_IMAGE"
        assert body["reason"] == "IMAGE_TOO_BLURRY"
        assert "disease" not in body

    def test_endpoint_json_symptom_backward_compatibility(self):
        """Existing JSON symptom request without file upload must still work cleanly."""
        payload = {"crop": "Tomato", "symptoms": ["yellow leaves", "stunted growth"]}
        resp = client.post("/api/v1/disease-detection", json=payload)
        assert resp.status_code == 200
        data = resp.json()
        assert "prediction" in data or "condition" in data
        assert "treatment" in data or "treatments" in data

"""Comprehensive Test Suite for Strict Plant Leaf Image Validation Gate.

Verifies:
1. Legitimate agricultural plant leaves (healthy, diseased, close-up, multiple crops) PASS validation.
2. Obvious non-plant images (laptop, phone, person, face, building, car, animal, random object, screenshot, document, blank, blurry, dark) FAIL validation.
3. The disease model is NEVER invoked for invalid non-plant images.
4. Response payloads conform to the specified API contracts.
"""

import asyncio
import io
from pathlib import Path
from unittest.mock import MagicMock, patch

import cv2
import numpy as np
import pytest
from PIL import Image, ImageDraw
from starlette.datastructures import UploadFile

from disease_pest_ai.validation.image_validator import (
    PlantLeafImageValidator,
    ValidationResult,
    get_image_validator,
)
from disease_pest_ai.api.routes.diagnose import detect_disease_frontend_compat

TEST_DATA_DIR = Path(__file__).resolve().parent.parent / "test_data"
FRONTEND_IMAGES_DIR = Path(__file__).resolve().parent.parent.parent.parent / "frontend" / "public" / "images"


@pytest.fixture(scope="module")
def validator():
    """Module-level validator instance."""
    return get_image_validator()


# --- Test Helper Image Generators ---

def create_synthetic_laptop() -> Image.Image:
    """Simulates a laptop image."""
    img = Image.new("RGB", (400, 300), color=(180, 180, 180))
    d = ImageDraw.Draw(img)
    d.rectangle([50, 40, 350, 220], fill=(20, 20, 20), outline=(100, 100, 100), width=4)
    d.rectangle([70, 60, 330, 200], fill=(50, 100, 200))  # Screen
    d.polygon([(30, 220), (370, 220), (390, 260), (10, 260)], fill=(120, 120, 120))  # Keyboard base
    return img


def create_synthetic_phone() -> Image.Image:
    """Simulates a mobile smartphone."""
    img = Image.new("RGB", (250, 450), color=(220, 220, 220))
    d = ImageDraw.Draw(img)
    d.rounded_rectangle([40, 30, 210, 420], radius=20, fill=(15, 15, 15))
    d.rectangle([55, 60, 195, 380], fill=(30, 80, 160))  # Screen
    d.ellipse([115, 40, 135, 50], fill=(50, 50, 50))  # Speaker
    return img


def create_synthetic_car() -> Image.Image:
    """Simulates a vehicle / car image."""
    img = Image.new("RGB", (450, 300), color=(190, 200, 210))
    d = ImageDraw.Draw(img)
    # Car body
    d.rectangle([60, 140, 390, 230], fill=(220, 30, 30))
    d.polygon([(120, 140), (170, 80), (310, 80), (350, 140)], fill=(200, 20, 20))
    # Windows
    d.polygon([(140, 135), (180, 90), (230, 90), (230, 135)], fill=(150, 210, 240))
    d.polygon([(240, 90), (300, 90), (330, 135), (240, 135)], fill=(150, 210, 240))
    # Wheels
    d.ellipse([100, 200, 160, 260], fill=(20, 20, 20))
    d.ellipse([290, 200, 350, 260], fill=(20, 20, 20))
    return img


def create_synthetic_building() -> Image.Image:
    """Simulates an architectural building."""
    img = Image.new("RGB", (400, 450), color=(135, 206, 235))  # Sky
    d = ImageDraw.Draw(img)
    d.rectangle([70, 100, 330, 450], fill=(130, 130, 130))
    for r in range(130, 410, 45):
        for c in range(95, 310, 45):
            d.rectangle([c, r, c + 25, r + 30], fill=(255, 255, 120))  # Windows
    return img


def create_synthetic_document() -> Image.Image:
    """Simulates a text document / paper."""
    img = Image.new("RGB", (400, 500), color=(255, 255, 255))
    d = ImageDraw.Draw(img)
    for y in range(40, 460, 20):
        d.line([(50, y), (350, y)], fill=(30, 30, 30), width=2)
    return img


def create_synthetic_ui_screenshot() -> Image.Image:
    """Simulates a UI web dashboard screenshot."""
    img = Image.new("RGB", (500, 350), color=(245, 247, 250))
    d = ImageDraw.Draw(img)
    d.rectangle([0, 0, 500, 40], fill=(40, 50, 70))  # Navbar
    d.rectangle([10, 50, 120, 340], fill=(230, 235, 240))  # Sidebar
    d.rectangle([140, 60, 280, 160], fill=(255, 255, 255), outline=(200, 200, 200))
    d.rectangle([300, 60, 480, 160], fill=(255, 255, 255), outline=(200, 200, 200))
    d.rectangle([140, 180, 480, 330], fill=(255, 255, 255), outline=(200, 200, 200))
    return img


def create_synthetic_random_object() -> Image.Image:
    """Simulates a random household object (coffee mug on desk)."""
    img = Image.new("RGB", (350, 350), color=(210, 180, 140))  # Wooden desk
    d = ImageDraw.Draw(img)
    # Mug body
    d.rectangle([120, 120, 220, 240], fill=(40, 80, 180))
    # Handle
    d.arc([190, 140, 260, 220], start=270, end=90, fill=(40, 80, 180), width=10)
    return img


def create_synthetic_animal() -> Image.Image:
    """Simulates an animal pattern (leopard / cat coat)."""
    img = Image.new("RGB", (350, 350), color=(218, 165, 32))  # Golden fur
    d = ImageDraw.Draw(img)
    for _ in range(50):
        x = np.random.randint(20, 330)
        y = np.random.randint(20, 330)
        r = np.random.randint(6, 15)
        d.ellipse([x - r, y - r, x + r, y + r], fill=(20, 20, 20))
    return img


# --- 1. Validation Tests for Real Agricultural Leaves ---

class TestValidPlantLeaves:
    """Verify that legitimate crop leaves pass validation with high confidence."""

    @pytest.mark.parametrize("filename,crop", [
        ("apple_scab_bierny.jpg", "Apple"),
        ("corn_common_rust.jpg", "Corn"),
        ("tomato_early_blight.jpg", "Tomato"),
        ("tomato_healthy.jpg", "Tomato"),
    ])
    def test_real_crop_leaves_pass_validation(self, validator, filename, crop):
        img_path = TEST_DATA_DIR / filename
        assert img_path.exists(), f"Sample image {filename} missing"
        img = Image.open(img_path).convert("RGB")

        res: ValidationResult = validator.validate(img)
        assert res.is_valid_plant_image is True, f"Failed on valid leaf {filename}: {res.reason} ({res.message})"
        assert res.status == "VALID"
        assert res.plant_confidence >= 0.75, f"Low plant confidence: {res.plant_confidence}"
        assert res.leaf_confidence >= 0.75, f"Low leaf confidence: {res.leaf_confidence}"
        assert res.reason is None


# --- 2. Validation Tests for Non-Plant Images ---

class TestInvalidNonPlantImages:
    """Verify that non-plant imagery is strictly rejected."""

    def test_laptop_image_rejected(self, validator):
        laptop = create_synthetic_laptop()
        res = validator.validate(laptop)
        assert res.is_valid_plant_image is False
        assert res.status == "INVALID_IMAGE"
        assert res.reason in ("NO_PLANT_DETECTED", "UNRELATED_IMAGE")
        assert res.plant_confidence < 0.70

    def test_phone_image_rejected(self, validator):
        phone = create_synthetic_phone()
        res = validator.validate(phone)
        assert res.is_valid_plant_image is False
        assert res.status == "INVALID_IMAGE"
        assert res.reason in ("NO_PLANT_DETECTED", "UNRELATED_IMAGE")

    def test_person_image_rejected(self, validator):
        farmer_path = FRONTEND_IMAGES_DIR / "farmer-profile.jpg"
        if farmer_path.exists():
            farmer_img = Image.open(farmer_path).convert("RGB")
            res = validator.validate(farmer_img)
            assert res.is_valid_plant_image is False
            assert res.status == "INVALID_IMAGE"
            assert res.reason in ("NO_PLANT_DETECTED", "UNRELATED_IMAGE")
            assert "person" in res.message.lower() or "no plant" in res.message.lower()

    def test_vehicle_image_rejected(self, validator):
        car = create_synthetic_car()
        res = validator.validate(car)
        assert res.is_valid_plant_image is False
        assert res.status == "INVALID_IMAGE"
        assert res.reason in ("NO_PLANT_DETECTED", "UNRELATED_IMAGE")

    def test_building_image_rejected(self, validator):
        building = create_synthetic_building()
        res = validator.validate(building)
        assert res.is_valid_plant_image is False
        assert res.status == "INVALID_IMAGE"
        assert res.reason in ("NO_PLANT_DETECTED", "UNRELATED_IMAGE")

    def test_animal_image_rejected(self, validator):
        animal = create_synthetic_animal()
        res = validator.validate(animal)
        assert res.is_valid_plant_image is False
        assert res.status == "INVALID_IMAGE"
        assert res.reason in ("NO_PLANT_DETECTED", "UNRELATED_IMAGE")

    def test_random_object_rejected(self, validator):
        mug = create_synthetic_random_object()
        res = validator.validate(mug)
        assert res.is_valid_plant_image is False
        assert res.status == "INVALID_IMAGE"
        assert res.reason in ("NO_PLANT_DETECTED", "UNRELATED_IMAGE")

    def test_document_rejected(self, validator):
        doc = create_synthetic_document()
        res = validator.validate(doc)
        assert res.is_valid_plant_image is False
        assert res.status == "INVALID_IMAGE"
        assert res.reason in ("UNRELATED_IMAGE", "NO_PLANT_DETECTED")

    def test_ui_screenshot_rejected(self, validator):
        ui = create_synthetic_ui_screenshot()
        res = validator.validate(ui)
        assert res.is_valid_plant_image is False
        assert res.status == "INVALID_IMAGE"
        assert res.reason in ("UNRELATED_IMAGE", "NO_PLANT_DETECTED")

    def test_blank_solid_image_rejected(self, validator):
        blank = Image.new("RGB", (300, 300), color=(255, 255, 255))
        res = validator.validate(blank)
        assert res.is_valid_plant_image is False
        assert res.status == "INVALID_IMAGE"
        assert res.reason == "LOW_IMAGE_QUALITY"

    def test_extremely_dark_image_rejected(self, validator):
        dark = Image.new("RGB", (300, 300), color=(8, 8, 8))
        res = validator.validate(dark)
        assert res.is_valid_plant_image is False
        assert res.status == "INVALID_IMAGE"
        assert res.reason in ("IMAGE_TOO_DARK", "LOW_IMAGE_QUALITY")

    def test_extremely_blurry_image_rejected(self, validator):
        leaf_path = TEST_DATA_DIR / "apple_scab_bierny.jpg"
        img = Image.open(leaf_path).convert("RGB")
        blurry_np = cv2.GaussianBlur(np.array(img), (61, 61), 0)
        blurry_img = Image.fromarray(blurry_np)

        res = validator.validate(blurry_img)
        assert res.is_valid_plant_image is False
        assert res.status == "INVALID_IMAGE"
        assert res.reason == "IMAGE_TOO_BLURRY"

    def test_low_resolution_image_rejected(self, validator):
        tiny_img = Image.new("RGB", (64, 64), color=(50, 180, 50))
        res = validator.validate(tiny_img)
        assert res.is_valid_plant_image is False
        assert res.status == "INVALID_IMAGE"
        assert res.reason == "LOW_IMAGE_QUALITY"


# --- 3. Critical Safety Gate Tests: Disease Model Must NOT Run on Invalid Images ---

class TestValidationGateEnforcement:
    """Verify that the disease model is never invoked when an image is invalid."""

    def test_disease_model_never_invoked_on_laptop(self):
        laptop_img = create_synthetic_laptop()
        buf = io.BytesIO()
        laptop_img.save(buf, format="JPEG")
        buf.seek(0)
        upload_file = UploadFile(filename="laptop.jpg", file=buf)

        with patch("disease_pest_ai.inference.pipeline.DiseasePestPipeline.predict") as mock_predict:
            res = asyncio.run(detect_disease_frontend_compat(
                file=upload_file,
                crop="Tomato",
            ))
            # The disease model MUST NOT have been called!
            assert not mock_predict.called, "CRITICAL ERROR: Disease model was called on a laptop image!"

            # Response structure verification
            assert res["success"] is False
            assert res["status"] == "INVALID_IMAGE"
            assert res["is_valid_plant_image"] is False
            assert "disease" not in res
            assert "disease_confidence" not in res
            assert res["reason"] in ("NO_PLANT_DETECTED", "UNRELATED_IMAGE")
            assert "message" in res

    def test_disease_model_invoked_only_on_valid_leaf(self):
        leaf_path = TEST_DATA_DIR / "tomato_early_blight.jpg"
        with open(leaf_path, "rb") as f:
            buf = io.BytesIO(f.read())
        upload_file = UploadFile(filename="tomato_early_blight.jpg", file=buf)

        res = asyncio.run(detect_disease_frontend_compat(
            file=upload_file,
            crop="Tomato",
        ))
        assert res["success"] is True
        assert res["status"] == "VALID"
        assert res["is_valid_plant_image"] is True
        assert "disease" in res
        assert "disease_confidence" in res
        assert "Early Blight" in res["disease"]
        assert res["data"]["confidence_percent"] >= 70

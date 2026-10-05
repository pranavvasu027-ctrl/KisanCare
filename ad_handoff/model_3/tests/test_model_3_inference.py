"""Inference verification test for Model 3: Crop Disease & Pest Diagnosis."""

import pytest
from pathlib import Path
import sys

# Ensure KisanCare root and model_3 directory are on path
KISANCARE_ROOT = Path(__file__).resolve().parent.parent.parent.parent
sys.path.insert(0, str(KISANCARE_ROOT))

M3_DIR = KISANCARE_ROOT / "ad_handoff" / "model_3"
sys.path.insert(0, str(M3_DIR))

from ad_handoff.model_3.model.loader import load_disease_model
from disease_pest_ai.knowledge_base.repository import KnowledgeBaseRepository
from disease_pest_ai.inference.pipeline import DiseasePestPipeline
from disease_pest_ai.schemas.final_output import AgricultureDiseaseResult


def test_model_3_full_pipeline_inference():
    """Verify Model 3: Artifact Load -> Preprocessing Load -> Valid Input -> Inference -> Valid Output."""
    # 1. MODEL ARTIFACT LOAD
    disease_checkpoint = load_disease_model()
    assert disease_checkpoint.exists()
    assert disease_checkpoint.stat().st_size > 10_000_000  # ~81 MB

    # 2. PREPROCESSING & KNOWLEDGE BASE LOAD
    kb_path = M3_DIR / "preprocessing" / "cibrc_database.json"
    assert kb_path.exists()
    repo = KnowledgeBaseRepository()
    treatments = repo.find_treatments(crop_name="Apple", condition="Apple Scab")
    assert treatments is not None

    # 3. VALID INPUT
    test_image_path = M3_DIR / "tests" / "apple_scab_bierny.jpg"
    assert test_image_path.exists()

    # 4. INFERENCE
    pipeline = DiseasePestPipeline()
    result = pipeline.predict(
        plant_image=str(test_image_path),
        crop_name="Apple",
        location_state="Himachal Pradesh",
        growth_stage="fruiting",
        image_type="leaf",
    )

    # 5. VALID OUTPUT
    assert isinstance(result, AgricultureDiseaseResult)
    assert result.disease is not None
    assert result.disease.condition == "Apple Scab"
    assert result.disease.score > 0.80
    assert result.disease.crop_match is True
    assert result.treatment is not None
    assert result.provenance is not None
    assert result.provenance.disease_model == "BiernyVR/crop-disease-classifier"
    assert result.provenance.pest_model == "underdogquality/yolo11s-pest-detection"
    assert "total_pipeline_ms" in result.provenance.latency_breakdown_ms

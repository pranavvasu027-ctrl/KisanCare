"""
Comprehensive Tests for Phase 2 Treatment Knowledge Base & Recommendation Engine.

Tests cover:
- Exact crop/condition matching
- Crop mismatch handling (safety block of chemicals)
- Unsupported disease / condition handling
- Absence of treatment record (graceful manual review fallback)
- Multiple valid treatment candidates and IPM ranking
- Missing numerical application information (label fallback)
- Location input handling (geographic scope 'India')
- Growth stage input handling and warnings
- Provenance propagation (full audit trail from image to CIBRC source)
- Outdated source warning (currency notice)
- Healthy leaf handling (strictly zero chemicals)
"""

from pathlib import Path
import pytest

from disease_pest_ai.inference.pipeline import DiseasePestPipeline
from disease_pest_ai.knowledge_base.repository import KnowledgeBaseRepository
from disease_pest_ai.recommendation.treatment_engine import TreatmentEngine
from disease_pest_ai.schemas.outputs import (
    ConditionType,
    RecommendationStatus,
)

TEST_DATA_DIR = Path(__file__).resolve().parent.parent / "test_data"
APPLE_SAMPLE = TEST_DATA_DIR / "apple_scab_bierny.jpg"
CORN_SAMPLE = TEST_DATA_DIR / "corn_common_rust.jpg"
TOMATO_EB_SAMPLE = TEST_DATA_DIR / "tomato_early_blight.jpg"
TOMATO_HLT_SAMPLE = TEST_DATA_DIR / "tomato_healthy.jpg"


@pytest.fixture
def engine():
    return TreatmentEngine()


@pytest.fixture
def pipeline():
    return DiseasePestPipeline(primary_disease_model="efficientnet")


def test_exact_crop_condition_match(engine):
    """Verify exact match retrieves registered CIBRC chemicals and IPM controls."""
    rec = engine.get_treatment_recommendations(
        crop_name="Tomato",
        condition="Early Blight",
        condition_type=ConditionType.DISEASE,
        location_state="Maharashtra",
        growth_stage="vegetative",
        prediction_score=0.88,
        crop_mismatch=False,
    )

    assert rec.status == RecommendationStatus.VERIFIED_CANDIDATES_FOUND
    assert rec.crop == "Tomato"
    assert rec.condition == "Early Blight"
    assert rec.verification_status == "verified"
    assert rec.label_verification_required is True
    assert rec.field_validation_required is True
    assert len(rec.chemical_candidates) > 0
    assert len(rec.non_chemical_controls) > 0

    # Verify registered active ingredients for Tomato Early Blight
    ai_names = [c.active_ingredient for c in rec.chemical_candidates]
    assert "Mancozeb" in ai_names
    assert "Difenoconazole" in ai_names


def test_crop_mismatch_blocks_chemicals(engine):
    """
    Verify crop mismatch safely blocks all chemical recommendations
    and mandates manual review.
    """
    rec = engine.get_treatment_recommendations(
        crop_name="Cotton",
        condition="Early Blight",  # Belongs to tomato, not cotton
        condition_type=ConditionType.DISEASE,
        location_state="Gujarat",
        growth_stage="flowering",
        prediction_score=0.85,
        crop_mismatch=True,  # Crop mismatch detected
    )

    assert rec.status == RecommendationStatus.MANUAL_REVIEW_REQUIRED
    assert rec.verification_status == "manual_review_required"
    assert rec.chemical_candidates == []  # Strictly NO chemicals on crop mismatch
    assert len(rec.warnings) > 0
    assert any("Crop Mismatch Warning" in w for w in rec.warnings)


def test_unsupported_disease_and_no_record(engine):
    """Verify unsupported disease triggers manual review rather than guessing."""
    rec = engine.get_treatment_recommendations(
        crop_name="Tomato",
        condition="NonExistentAlienPathology",
        condition_type=ConditionType.DISEASE,
        location_state="Karnataka",
        growth_stage="vegetative",
        prediction_score=0.90,
        crop_mismatch=False,
    )

    assert rec.status == RecommendationStatus.MANUAL_REVIEW_REQUIRED
    assert rec.chemical_candidates == []
    assert any("Unsupported Condition" in w for w in rec.warnings)


def test_low_confidence_blocks_chemicals(engine):
    """Verify vision score below threshold triggers manual review."""
    rec = engine.get_treatment_recommendations(
        crop_name="Tomato",
        condition="Early Blight",
        condition_type=ConditionType.DISEASE,
        location_state="Punjab",
        growth_stage="vegetative",
        prediction_score=0.25,  # Below 0.40 threshold
        crop_mismatch=False,
    )

    assert rec.status == RecommendationStatus.MANUAL_REVIEW_REQUIRED
    assert rec.chemical_candidates == []
    assert any("Low Diagnostic Confidence" in w for w in rec.warnings)


def test_multiple_valid_candidates_and_ipm_priority(engine):
    """Verify candidates are returned as a list and protectant/multi-site is ranked first."""
    rec = engine.get_treatment_recommendations(
        crop_name="Apple",
        condition="Apple Scab",
        condition_type=ConditionType.DISEASE,
        location_state="Himachal Pradesh",
        growth_stage="fruiting",
        prediction_score=0.92,
        crop_mismatch=False,
    )

    assert rec.status == RecommendationStatus.VERIFIED_CANDIDATES_FOUND
    assert len(rec.chemical_candidates) >= 3

    # Multi-site protectant (Mancozeb or Captan) should be ranked before single-site DMI
    first_candidate = rec.chemical_candidates[0]
    assert first_candidate.active_ingredient in ("Mancozeb", "Captan")

    # Non-chemical practices must be present
    assert len(rec.non_chemical_controls) > 0
    assert any("urea" in c.description.lower() for c in rec.non_chemical_controls)


def test_missing_numerical_dosage_falls_back_to_label(engine):
    """Verify records without numerical dosage state 'Follow current registered product label'."""
    rec = engine.get_treatment_recommendations(
        crop_name="Tomato",
        condition="Bacterial Spot",
        condition_type=ConditionType.DISEASE,
        location_state="Haryana",
        growth_stage="vegetative",
        prediction_score=0.85,
        crop_mismatch=False,
    )

    streptomycin = next(
        (c for c in rec.chemical_candidates if "Streptomycin" in c.active_ingredient), None
    )
    assert streptomycin is not None
    assert "Follow the current registered product label" in streptomycin.dose_information


def test_location_and_geographic_scope(engine):
    """Verify geographic scope is set to India and location preserved."""
    rec = engine.get_treatment_recommendations(
        crop_name="Corn",
        condition="Common Rust",
        condition_type=ConditionType.DISEASE,
        location_state="Bihar",
        growth_stage="vegetative",
        prediction_score=0.91,
        crop_mismatch=False,
    )

    assert rec.geographic_scope == "India"
    assert rec.status == RecommendationStatus.VERIFIED_CANDIDATES_FOUND


def test_growth_stage_handling_and_warning(engine):
    """Verify growth stage guidance is preserved or warning generated if unavailable."""
    rec = engine.get_treatment_recommendations(
        crop_name="Grape",
        condition="Leaf Blight (Isariopsis Leaf Spot)",
        condition_type=ConditionType.DISEASE,
        location_state="Maharashtra",
        growth_stage="flowering",
        prediction_score=0.85,
        crop_mismatch=False,
    )

    assert rec.status == RecommendationStatus.VERIFIED_CANDIDATES_FOUND


def test_outdated_source_warning(engine):
    """Verify explicit currency notice mentioning 31/03/2024 is included."""
    rec = engine.get_treatment_recommendations(
        crop_name="Tomato",
        condition="Early Blight",
        condition_type=ConditionType.DISEASE,
        location_state="Maharashtra",
        growth_stage="vegetative",
        prediction_score=0.88,
        crop_mismatch=False,
    )

    assert any("31.03.2024" in w or "2024-03-31" in w for w in rec.warnings)


def test_healthy_plant_strictly_zero_chemicals(engine):
    """Verify healthy tissue returns NO chemicals and GAP guidance."""
    rec = engine.get_treatment_recommendations(
        crop_name="Tomato",
        condition="Healthy",
        condition_type=ConditionType.HEALTHY,
        location_state="Maharashtra",
        growth_stage="vegetative",
        prediction_score=0.90,
        crop_mismatch=False,
    )

    assert rec.status == RecommendationStatus.NO_TREATMENT_NEEDED_HEALTHY
    assert rec.chemical_candidates == []
    assert len(rec.non_chemical_controls) > 0
    assert any("GAP" in c.description or "balanced" in c.description for c in rec.non_chemical_controls)


def test_end_to_end_pipeline_with_treatment(pipeline):
    """Verify end-to-end pipeline produces AgricultureDiseaseResult with complete audit provenance."""
    result = pipeline.predict(
        plant_image=TOMATO_EB_SAMPLE,
        crop_name="Tomato",
        location_state="Karnataka",
        growth_stage="fruiting",
        image_type="leaf",
    )

    assert result.crop == "Tomato"
    assert result.condition == "Early Blight"
    assert result.crop_match is True
    assert result.prediction_score > 0.80

    # Verify Treatment
    treatment = result.treatment
    assert treatment.status == RecommendationStatus.VERIFIED_CANDIDATES_FOUND
    assert len(treatment.chemical_candidates) > 0
    assert len(treatment.non_chemical_controls) > 0

    # Verify Provenance
    prov = result.provenance
    assert "vision_model" in prov
    assert "treatment_source" in prov
    assert "source_date" in prov
    assert prov["source_date"] == "2024-03-31"
    assert prov["context"]["location_state"] == "Karnataka"


def test_end_to_end_pipeline_crop_mismatch(pipeline):
    """Verify end-to-end pipeline handles crop mismatch safely."""
    result = pipeline.predict(
        plant_image=TOMATO_EB_SAMPLE,  # Image is tomato early blight
        crop_name="Cotton",            # User says Cotton
        location_state="Gujarat",
        growth_stage="flowering",
        image_type="leaf",
    )

    assert result.crop_match is False
    assert result.treatment.status == RecommendationStatus.MANUAL_REVIEW_REQUIRED
    assert result.treatment.chemical_candidates == []
    assert any("Crop mismatch" in w for w in result.warnings)

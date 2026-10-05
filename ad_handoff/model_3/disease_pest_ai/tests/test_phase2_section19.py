"""
Unit and Integration Tests for Phase 2 Requirements (Section 19: 15 Test Cases).

Test Cases:
 1. valid crop + disease match
 2. valid crop + pest match
 3. crop mismatch
 4. unsupported disease
 5. unsupported pest
 6. no treatment record
 7. multiple valid treatments
 8. missing dose information
 9. missing stage-specific information
10. location/state input
11. provenance preservation
12. outdated source warning
13. low-confidence diagnosis
14. healthy plant
15. unknown condition
"""

import pytest
from disease_pest_ai.knowledge_base.repository import KnowledgeBaseRepository
from disease_pest_ai.recommendation.treatment_engine import TreatmentEngine
from disease_pest_ai.schemas.outputs import (
    ConditionType,
    ReasonCode,
    RecommendationStatus,
)


@pytest.fixture
def engine():
    return TreatmentEngine()


def test_01_valid_crop_disease_match(engine):
    """1. Valid crop + disease match -> returns verified candidates and IPM controls."""
    rec = engine.get_treatment_recommendations(
        crop_name="Tomato",
        condition="Tomato Early Blight",
        condition_type=ConditionType.DISEASE,
        location_state="Maharashtra",
        growth_stage="vegetative",
        prediction_score=0.92,
        crop_mismatch=False,
    )
    assert rec.status == RecommendationStatus.VERIFIED_CANDIDATES_FOUND
    assert rec.reason_code is None
    assert rec.crop == "Tomato"
    assert len(rec.chemical_candidates) > 0
    assert len(rec.non_chemical_controls) > 0
    assert rec.verification_status == "verified"
    assert rec.label_verification_required is True
    assert rec.field_validation_required is True


def test_02_valid_crop_pest_match(engine):
    """2. Valid crop + pest match -> returns verified pest treatments."""
    rec = engine.get_treatment_recommendations(
        crop_name="Cotton",
        condition="Cotton Bollworm Infestation",
        condition_type=ConditionType.PEST,
        location_state="Gujarat",
        growth_stage="boll_formation",
        prediction_score=0.89,
        crop_mismatch=False,
    )
    assert rec.status == RecommendationStatus.VERIFIED_CANDIDATES_FOUND
    assert rec.condition_type == ConditionType.PEST
    assert len(rec.chemical_candidates) > 0
    assert any("Chlorantraniliprole" in c.active_ingredient for c in rec.chemical_candidates)
    assert len(rec.non_chemical_controls) > 0
    assert any("trap" in c.description.lower() or "trichogramma" in c.description.lower() for c in rec.non_chemical_controls)


def test_03_crop_mismatch(engine):
    """3. Crop mismatch -> status manual_review_required, code CROP_CONDITION_MISMATCH, 0 chemicals."""
    rec = engine.get_treatment_recommendations(
        crop_name="Wheat",
        condition="Tomato Early Blight",
        condition_type=ConditionType.DISEASE,
        location_state="Punjab",
        growth_stage="tillering",
        prediction_score=0.91,
        crop_mismatch=True,
    )
    assert rec.status == RecommendationStatus.MANUAL_REVIEW_REQUIRED
    assert rec.reason_code == ReasonCode.CROP_CONDITION_MISMATCH
    assert rec.chemical_candidates == []
    assert any("Crop Mismatch Warning" in w for w in rec.warnings)


def test_04_unsupported_disease(engine):
    """4. Unsupported disease -> status manual_review_required, code UNSUPPORTED_CONDITION."""
    rec = engine.get_treatment_recommendations(
        crop_name="Tomato",
        condition="Dragonfruit Anthracnose",
        condition_type=ConditionType.DISEASE,
        location_state="Tamil Nadu",
        growth_stage="vegetative",
        prediction_score=0.88,
        crop_mismatch=False,
    )
    assert rec.status == RecommendationStatus.MANUAL_REVIEW_REQUIRED
    assert rec.reason_code == ReasonCode.UNSUPPORTED_CONDITION
    assert rec.chemical_candidates == []
    assert any("Unsupported Condition" in w for w in rec.warnings)


def test_05_unsupported_pest(engine):
    """5. Unsupported pest -> status manual_review_required, code UNSUPPORTED_CONDITION."""
    rec = engine.get_treatment_recommendations(
        crop_name="Tomato",
        condition="Locust Swarm",
        condition_type=ConditionType.PEST,
        location_state="Rajasthan",
        growth_stage="vegetative",
        prediction_score=0.85,
        crop_mismatch=False,
    )
    assert rec.status == RecommendationStatus.MANUAL_REVIEW_REQUIRED
    assert rec.reason_code == ReasonCode.UNSUPPORTED_CONDITION
    assert rec.chemical_candidates == []


def test_06_no_treatment_record(engine, monkeypatch):
    """6. No treatment record -> recognized crop and condition but 0 treatments -> NO_VERIFIED_TREATMENT."""
    # Temporarily make find_treatments return empty list to simulate missing treatment
    monkeypatch.setattr(engine.repository, "find_treatments", lambda *args, **kwargs: [])
    rec = engine.get_treatment_recommendations(
        crop_name="Tomato",
        condition="Early Blight",
        condition_type=ConditionType.DISEASE,
        location_state="Karnataka",
        growth_stage="vegetative",
        prediction_score=0.85,
        crop_mismatch=False,
    )
    assert rec.status == RecommendationStatus.MANUAL_REVIEW_REQUIRED
    assert rec.reason_code == ReasonCode.NO_VERIFIED_TREATMENT
    assert rec.chemical_candidates == []
    assert any("No verified treatment records found" in w for w in rec.warnings)


def test_07_multiple_valid_treatments(engine):
    """7. Multiple valid treatments -> returned as ranked list with multi-site contact protectant first."""
    rec = engine.get_treatment_recommendations(
        crop_name="Apple",
        condition="Apple Scab",
        condition_type=ConditionType.DISEASE,
        location_state="Himachal Pradesh",
        growth_stage="fruiting",
        prediction_score=0.95,
        crop_mismatch=False,
    )
    assert rec.status == RecommendationStatus.VERIFIED_CANDIDATES_FOUND
    assert len(rec.chemical_candidates) >= 3
    # Check ranking: multi-site contact protectant (Mancozeb or Captan) ranked ahead of single-site DMIs
    first_candidate = rec.chemical_candidates[0]
    assert first_candidate.active_ingredient in ("Mancozeb", "Captan")


def test_08_missing_dose_information(engine):
    """8. Missing dose information -> never invented, falls back to registered product label."""
    rec = engine.get_treatment_recommendations(
        crop_name="Tomato",
        condition="Bacterial Spot",
        condition_type=ConditionType.DISEASE,
        location_state="Haryana",
        growth_stage="vegetative",
        prediction_score=0.87,
        crop_mismatch=False,
    )
    streptomycin = next(
        (c for c in rec.chemical_candidates if "Streptomycin" in c.active_ingredient), None
    )
    assert streptomycin is not None
    assert "Follow the current registered product label" in streptomycin.dose_information


def test_09_missing_stage_specific_information(engine):
    """9. Missing stage-specific information -> returns 'unavailable', does not fabricate restrictions."""
    rec = engine.get_treatment_recommendations(
        crop_name="Grape",
        condition="Leaf Blight (Isariopsis Leaf Spot)",
        condition_type=ConditionType.DISEASE,
        location_state="Maharashtra",
        growth_stage="flowering",
        prediction_score=0.85,
        crop_mismatch=False,
    )
    assert rec.stage_specific_guidance == "unavailable"
    assert any("Growth stage 'flowering' specified" in w for w in rec.warnings)


def test_10_location_state_input(engine):
    """10. Location/state input preserved without fabricating state-level restrictions."""
    rec = engine.get_treatment_recommendations(
        crop_name="Corn",
        condition="Common Rust",
        condition_type=ConditionType.DISEASE,
        location_state="Madhya Pradesh",
        growth_stage="vegetative",
        prediction_score=0.90,
        crop_mismatch=False,
    )
    assert rec.geographic_scope == "India"
    assert rec.status == RecommendationStatus.VERIFIED_CANDIDATES_FOUND


def test_11_provenance_preservation(engine):
    """11. Provenance preservation -> source_id, title, url, source_date attached."""
    rec = engine.get_treatment_recommendations(
        crop_name="Tomato",
        condition="Early Blight",
        condition_type=ConditionType.DISEASE,
        location_state="Maharashtra",
        growth_stage="vegetative",
        prediction_score=0.90,
        crop_mismatch=False,
    )
    assert len(rec.source_records) > 0
    src = rec.source_records[0]
    assert "source_id" in src
    assert "title" in src
    assert "url" in src
    assert "source_date" in src
    assert src["source_date"] in ("2024-03-31", "2022-06-15", "2023-01-10")


def test_12_outdated_source_warning(engine):
    """12. Outdated source warning -> statutory currency notice always included."""
    rec = engine.get_treatment_recommendations(
        crop_name="Tomato",
        condition="Early Blight",
        condition_type=ConditionType.DISEASE,
        location_state="Maharashtra",
        growth_stage="vegetative",
        prediction_score=0.88,
        crop_mismatch=False,
    )
    assert any("2024-03-31" in w or "31.03.2024" in w for w in rec.warnings)
    assert any("Regulatory Currency Notice" in w for w in rec.warnings)


def test_13_low_confidence_diagnosis(engine):
    """13. Low-confidence diagnosis (<0.40) -> status manual_review_required, code LOW_MODEL_SCORE."""
    rec = engine.get_treatment_recommendations(
        crop_name="Tomato",
        condition="Early Blight",
        condition_type=ConditionType.DISEASE,
        location_state="Maharashtra",
        growth_stage="vegetative",
        prediction_score=0.35,  # Below threshold
        crop_mismatch=False,
    )
    assert rec.status == RecommendationStatus.MANUAL_REVIEW_REQUIRED
    assert rec.reason_code == ReasonCode.LOW_MODEL_SCORE
    assert rec.chemical_candidates == []
    assert any("Low Diagnostic Confidence" in w for w in rec.warnings)


def test_14_healthy_plant(engine):
    """14. Healthy plant -> status no_treatment_needed_healthy, strictly 0 chemicals, GAP guidance."""
    rec = engine.get_treatment_recommendations(
        crop_name="Tomato",
        condition="Healthy",
        condition_type=ConditionType.HEALTHY,
        location_state="Maharashtra",
        growth_stage="vegetative",
        prediction_score=0.95,
        crop_mismatch=False,
    )
    assert rec.status == RecommendationStatus.NO_TREATMENT_NEEDED_HEALTHY
    assert rec.chemical_candidates == []
    assert len(rec.non_chemical_controls) > 0
    assert rec.label_verification_required is False


def test_15_unknown_condition(engine):
    """15. Unknown condition -> status manual_review_required, reason code UNSUPPORTED_CONDITION."""
    rec = engine.get_treatment_recommendations(
        crop_name="Tomato",
        condition="Unknown Strange Disease",
        condition_type=ConditionType.UNKNOWN,
        location_state="Maharashtra",
        growth_stage="vegetative",
        prediction_score=0.50,
        crop_mismatch=False,
    )
    assert rec.status == RecommendationStatus.MANUAL_REVIEW_REQUIRED
    assert rec.reason_code == ReasonCode.UNSUPPORTED_CONDITION
    assert rec.chemical_candidates == []

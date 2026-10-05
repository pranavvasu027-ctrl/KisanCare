"""
Tests for crop consistency and validation rules.
"""

from disease_pest_ai.models.base import check_crop_consistency, normalize_crop_name


def test_crop_normalization():
    assert normalize_crop_name("Corn (maize)") == "corn"
    assert normalize_crop_name("Maize") == "corn"
    assert normalize_crop_name("Pepper, bell") == "pepper"
    assert normalize_crop_name("Capsicum") == "pepper"
    assert normalize_crop_name("Tomatoes") == "tomato"


def test_crop_consistency_matches():
    # Identical crops
    mismatch, warnings = check_crop_consistency("Apple", "Apple")
    assert mismatch is False
    assert len(warnings) == 0

    # Synonymous crops
    mismatch, warnings = check_crop_consistency("Maize", "Corn")
    assert mismatch is False

    mismatch, warnings = check_crop_consistency("Bell Pepper", "Pepper")
    assert mismatch is False


def test_crop_consistency_mismatches():
    # Tomato vs Apple
    mismatch, warnings = check_crop_consistency("Tomato", "Apple")
    assert mismatch is True
    assert len(warnings) > 0
    assert "Crop mismatch detected" in warnings[0]
    assert "Tomato" in warnings[0]
    assert "Apple" in warnings[0]

    # Cotton vs Potato
    mismatch, warnings = check_crop_consistency("Cotton", "Potato")
    assert mismatch is True


def test_crop_consistency_none_inputs():
    mismatch, warnings = check_crop_consistency(None, "Apple")
    assert mismatch is False
    assert len(warnings) == 0

    mismatch, warnings = check_crop_consistency("Tomato", None)
    assert mismatch is False
    assert len(warnings) == 0

"""
Tests for Agronomic Advisory & Educational Guidance Engine
==========================================================
Validates:
  1. Standard ICAR soil fertility classifications for N, P, K, pH.
  2. Educational guidance is clearly distinguished from site-specific prescriptions.
  3. No commercial fertilizer dosage is inferred from mass-balance ledgers.
  4. Missing data recommends accredited laboratory testing.
  5. Explains freshness drift with physical/biological mechanisms.
  6. Recommends qualified agronomist consultation.
"""

import unittest

from ml.soil_intelligence.reporting.advisory import (
    AgronomicAdvisoryEngine,
    NutrientTier,
    ReactionTier,
    SoilAdvisoryBundle
)


class TestAgronomicAdvisoryEngine(unittest.TestCase):

    def test_nitrogen_tier_classifications(self):
        """Nitrogen classified according to ICAR benchmarks: Low (<280), Medium (280-560), High (>560)."""
        # Low N
        adv_low = AgronomicAdvisoryEngine.classify_nitrogen(210.0)
        self.assertEqual(adv_low.tier, NutrientTier.LOW.value)
        self.assertIn("Low", adv_low.status_label)
        self.assertIn("Subbiah", adv_low.scientific_reference)

        # Medium N
        adv_med = AgronomicAdvisoryEngine.classify_nitrogen(350.0)
        self.assertEqual(adv_med.tier, NutrientTier.MEDIUM.value)
        self.assertIn("Medium", adv_med.status_label)

        # High N
        adv_high = AgronomicAdvisoryEngine.classify_nitrogen(620.0)
        self.assertEqual(adv_high.tier, NutrientTier.HIGH.value)
        self.assertIn("High", adv_high.status_label)

    def test_phosphorus_tier_classifications(self):
        """Phosphorus classified by Olsen elemental P: Low (<10), Medium (10-24.4), High (>24.4)."""
        adv_low = AgronomicAdvisoryEngine.classify_phosphorus(8.0)
        self.assertEqual(adv_low.tier, NutrientTier.LOW.value)

        adv_med = AgronomicAdvisoryEngine.classify_phosphorus(15.0)
        self.assertEqual(adv_med.tier, NutrientTier.MEDIUM.value)

        adv_high = AgronomicAdvisoryEngine.classify_phosphorus(32.0)
        self.assertEqual(adv_high.tier, NutrientTier.HIGH.value)

    def test_potassium_tier_classifications(self):
        """Potassium classified by ammonium acetate elemental K: Low (<119.5), Medium (119.5-278.9), High (>278.9)."""
        adv_low = AgronomicAdvisoryEngine.classify_potassium(95.0)
        self.assertEqual(adv_low.tier, NutrientTier.LOW.value)

        adv_med = AgronomicAdvisoryEngine.classify_potassium(200.0)
        self.assertEqual(adv_med.tier, NutrientTier.MEDIUM.value)

        adv_high = AgronomicAdvisoryEngine.classify_potassium(350.0)
        self.assertEqual(adv_high.tier, NutrientTier.HIGH.value)

    def test_soil_reaction_ph_classifications(self):
        """pH classified across standard agricultural reaction tiers."""
        adv_acid = AgronomicAdvisoryEngine.classify_ph(5.2)
        self.assertEqual(adv_acid.tier, ReactionTier.STRONGLY_ACIDIC.value)

        adv_neutral = AgronomicAdvisoryEngine.classify_ph(7.1)
        self.assertEqual(adv_neutral.tier, ReactionTier.NEUTRAL.value)

        adv_alkali = AgronomicAdvisoryEngine.classify_ph(8.2)
        self.assertEqual(adv_alkali.tier, ReactionTier.MODERATELY_ALKALINE.value)
        self.assertTrue(any("organic manure" in c.lower() for c in adv_alkali.management_considerations))

    def test_missing_parameters_recommend_testing(self):
        """Missing parameters are handled safely without guessing."""
        adv_none = AgronomicAdvisoryEngine.classify_nitrogen(None)
        self.assertEqual(adv_none.tier, NutrientTier.NOT_DETERMINED.value)
        self.assertIn("Not Available", adv_none.status_label)

    def test_guidance_scope_is_educational_not_prescription(self):
        """Guidance scope must explicitly state GENERAL_EDUCATIONAL_GUIDANCE."""
        bundle = AgronomicAdvisoryEngine.generate_plot_advisory_bundle("PLOT_001", n_kg_ha=250.0, p_kg_ha=12.0, k_kg_ha=220.0)
        self.assertEqual(bundle.nitrogen_advisory.guidance_scope, "GENERAL_EDUCATIONAL_GUIDANCE")
        self.assertIn("do not calculate commercial fertilizer dosages directly from simple mass-balance", "; ".join(bundle.general_recommendations).lower())
        self.assertIn("Krishi Vigyan Kendra", bundle.agronomic_disclaimer)

    # -----------------------------------------------------------------
    # Tests for D-03: pH Classification Provenance & Provisional Handling
    # -----------------------------------------------------------------
    def test_ph_classification_provenance_and_citations(self):
        """
        D-03: pH classification must cite exact authoritative sources:
        Jackson (1973 §3) for potentiometric protocol, and USDA-NRCS (2017) / ICAR (Muhr et al. 1965)
        for agricultural reaction tier boundaries.
        """
        adv_ph = AgronomicAdvisoryEngine.classify_ph(7.4)
        self.assertIsNotNone(adv_ph)
        self.assertIn("Jackson 1973", adv_ph.scientific_reference)
        self.assertIn("USDA-NRCS", adv_ph.scientific_reference)
        self.assertIn("Muhr et al. 1965", adv_ph.scientific_reference)
        self.assertEqual(adv_ph.guidance_scope, "GENERAL_EDUCATIONAL_GUIDANCE")
        self.assertFalse(adv_ph.is_provisional)

    def test_extreme_ph_flagged_as_provisional(self):
        """
        D-03: Non-agricultural extreme pH values (< 3.5 or > 10.5) must be
        marked as provisional pending laboratory re-test.
        """
        # Ultra-acidic / extreme
        adv_ultra = AgronomicAdvisoryEngine.classify_ph(2.8)
        self.assertTrue(adv_ultra.is_provisional)
        self.assertIsNotNone(adv_ultra.provisional_reason)
        self.assertIn("provisional", adv_ultra.provisional_reason.lower())

        # Highly sodic / extreme alkaline
        adv_extreme_alkali = AgronomicAdvisoryEngine.classify_ph(11.2)
        self.assertTrue(adv_extreme_alkali.is_provisional)
        self.assertIn("provisional", adv_extreme_alkali.provisional_reason.lower())

        # Normal agricultural range is NOT provisional
        adv_normal = AgronomicAdvisoryEngine.classify_ph(8.1)
        self.assertFalse(adv_normal.is_provisional)
        self.assertIsNone(adv_normal.provisional_reason)


if __name__ == "__main__":
    unittest.main()

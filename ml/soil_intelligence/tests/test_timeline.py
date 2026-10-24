"""
Unit Tests for Dynamic Multi-Year Timeline & Agronomic Depletion Engine
=======================================================================
Verifies event ordering, irregular multi-year timelines (2023-2026),
crop removal benchmarks, biological N2 fixation credits, fertilizer additions,
cumulative mass-balance ledgers, uncertainty propagation, and abstention rules.
"""

import unittest
from ml.soil_intelligence.schemas import (
    MeasuredLaboratoryReport,
    ModelledEnvironmentalContext,
    ProvenanceType
)
from ml.soil_intelligence.timeline.agronomic_depletion import (
    AgronomicDepletionEngine,
    CROP_REMOVAL_BENCHMARKS,
    FERTILIZER_GRADE_BENCHMARKS
)
from ml.soil_intelligence.timeline.timeline_manager import (
    PlotTimelineManager,
    TimelineSufficiencyAssessment
)


class TestAgronomicDepletionEngine(unittest.TestCase):

    def test_cereal_crop_removal_wheat(self):
        """Wheat removal: 24.5 kg N, 3.8 kg elemental P, 20.0 kg elemental K per ton."""
        flux = AgronomicDepletionEngine.calculate_crop_removal(
            crop_name="Wheat",
            yield_tons_ha=3.0,
            event_date="2024-04-10"
        )
        self.assertEqual(flux.delta_n_kg_ha, -73.5)            # 3 * 24.5
        self.assertEqual(flux.delta_p_elemental_kg_ha, -11.4)  # 3 * 3.8
        self.assertEqual(flux.delta_k_elemental_kg_ha, -60.0)  # 3 * 20.0
        self.assertIn("Wheat", flux.description)

    def test_legume_bnf_credit_soybean(self):
        """Soybean biological N2 fixation credits 55% of N uptake from air."""
        flux = AgronomicDepletionEngine.calculate_crop_removal(
            crop_name="Soybean",
            yield_tons_ha=2.0,
            event_date="2024-10-15"
        )
        # Total uptake = 2 * 65 = 130 kg N, but 55% is fixed; net soil depletion = 130 * 0.45 = 58.5 kg N
        self.assertEqual(flux.delta_n_kg_ha, -58.5)
        self.assertEqual(flux.delta_p_elemental_kg_ha, -12.0)  # 2 * 6.0
        self.assertTrue(any("fixation" in a.lower() for a in flux.assumptions))

    def test_straw_retention_potassium_credit(self):
        """When straw is retained on field, ~75% of wheat vegetative K is preserved."""
        flux_removed = AgronomicDepletionEngine.calculate_crop_removal(
            crop_name="Wheat",
            yield_tons_ha=4.0,
            event_date="2024-04-10",
            residue_retained=False
        )
        flux_retained = AgronomicDepletionEngine.calculate_crop_removal(
            crop_name="Wheat",
            yield_tons_ha=4.0,
            event_date="2024-04-10",
            residue_retained=True
        )
        # 4 tons * 20 kg K = 80 kg K total. Retaining straw keeps 75%, so net removal is only 25% = 20 kg K
        self.assertEqual(flux_removed.delta_k_elemental_kg_ha, -80.0)
        self.assertEqual(flux_retained.delta_k_elemental_kg_ha, -20.0)

    def test_mineral_fertilizer_addition(self):
        """Urea (46% N), DAP (18% N, 46% P2O5), MOP (60% K2O)."""
        # 100 kg Urea = 46 kg N
        urea_flux = AgronomicDepletionEngine.calculate_fertilizer_input("Urea", 100.0, "2024-06-15")
        self.assertEqual(urea_flux.delta_n_kg_ha, 46.0)
        self.assertEqual(urea_flux.delta_p_elemental_kg_ha, 0.0)

        # 100 kg DAP = 18 kg N, 46% P2O5 -> 20.08 kg elemental P
        dap_flux = AgronomicDepletionEngine.calculate_fertilizer_input("DAP", 100.0, "2024-06-15")
        self.assertEqual(dap_flux.delta_n_kg_ha, 18.0)
        self.assertAlmostEqual(dap_flux.delta_p_elemental_kg_ha, 20.08, places=1)

        # 100 kg MOP = 60% K2O -> 49.81 kg elemental K
        mop_flux = AgronomicDepletionEngine.calculate_fertilizer_input("MOP", 100.0, "2024-06-15")
        self.assertAlmostEqual(mop_flux.delta_k_elemental_kg_ha, 49.81, places=1)

    def test_organic_manure_mineralization_kinetics(self):
        """Farmyard manure (FYM) credits 30% first-year availability for N."""
        # 10,000 kg FYM (10 tons) @ 0.5% N = 50 kg total N * 30% Year-1 = 15 kg N available
        fym_flux = AgronomicDepletionEngine.calculate_fertilizer_input("FYM", 10000.0, "2024-05-01")
        self.assertEqual(fym_flux.delta_n_kg_ha, 15.0)
        self.assertTrue(any("mineralization" in a.lower() for a in fym_flux.assumptions))

    def test_invalid_rates_rejected(self):
        """Zero or negative fertilizer application rates must raise ValueError."""
        with self.assertRaises(ValueError):
            AgronomicDepletionEngine.calculate_fertilizer_input("Urea", 0.0, "2024-01-01")
        with self.assertRaises(ValueError):
            AgronomicDepletionEngine.calculate_crop_removal("Wheat", -2.0, "2024-01-01")

    # -----------------------------------------------------------------
    # Tests for D-02: Yield Plausibility Safeguards
    # -----------------------------------------------------------------
    def test_yield_within_crop_specific_bounds_accepted(self):
        """Standard wheat yield (4.0 t/ha) within plausible threshold (8.5 t/ha) passes without review flags."""
        flux = AgronomicDepletionEngine.calculate_crop_removal("Wheat", 4.0, "2024-04-10")
        self.assertFalse(flux.review_required)
        self.assertEqual(flux.review_flags, [])
        self.assertEqual(flux.raw_reported_yield_tons_ha, 4.0)
        self.assertEqual(flux.delta_n_kg_ha, -98.0)  # 4.0 * 24.5

    def test_wheat_yield_exceeding_bound_flags_suspicious_high_yield(self):
        """
        D-02: Extreme wheat yield (15.0 t/ha > 8.5 t/ha) flags SUSPICIOUS_HIGH_YIELD,
        requires human review, preserves raw reported yield verbatim, and does NOT silently clamp.
        """
        flux = AgronomicDepletionEngine.calculate_crop_removal("Wheat", 15.0, "2024-04-10")
        self.assertTrue(flux.review_required)
        self.assertEqual(flux.raw_reported_yield_tons_ha, 15.0)
        self.assertTrue(any("SUSPICIOUS_HIGH_YIELD" in f for f in flux.review_flags))
        # Verify NO silent clamping occurred: 15 * 24.5 = 367.5 kg N removal is preserved
        self.assertEqual(flux.delta_n_kg_ha, -367.5)
        self.assertTrue(any("exceeds maximum plausible bound" in a for a in flux.assumptions))

    def test_crop_specific_plausibility_bounds_not_blanket(self):
        """
        D-02: Crop-specific plausibility ranges are applied, NOT blanket cereal/legume thresholds.
        Sugarcane normal yield (120 t/ha) passes, but > 180 t/ha flags review.
        Cotton normal yield (3.0 t/ha) passes, but > 4.5 t/ha flags review.
        """
        # Sugarcane: 120 t/ha is typical for Adsali sugarcane in Maharashtra
        cane_normal = AgronomicDepletionEngine.calculate_crop_removal("Sugarcane", 120.0, "2024-03-01")
        self.assertFalse(cane_normal.review_required)

        # Sugarcane: 250 t/ha exceeds max bound (180 t/ha)
        cane_high = AgronomicDepletionEngine.calculate_crop_removal("Sugarcane", 250.0, "2024-03-01")
        self.assertTrue(cane_high.review_required)
        self.assertTrue(any("SUSPICIOUS_HIGH_YIELD" in f for f in cane_high.review_flags))
        self.assertEqual(cane_high.raw_reported_yield_tons_ha, 250.0)

        # Cotton: 3.0 t/ha is plausible under irrigation
        cotton_normal = AgronomicDepletionEngine.calculate_crop_removal("Cotton", 3.0, "2024-11-01")
        self.assertFalse(cotton_normal.review_required)

        # Cotton: 10.0 t/ha exceeds max bound (4.5 t/ha)
        cotton_high = AgronomicDepletionEngine.calculate_crop_removal("Cotton", 10.0, "2024-11-01")
        self.assertTrue(cotton_high.review_required)
        self.assertTrue(any("SUSPICIOUS_HIGH_YIELD" in f for f in cotton_high.review_flags))

    def test_unsupported_crop_no_defensible_threshold_requires_review(self):
        """
        D-02: When no defensible threshold exists for an unsupported crop,
        flag for review rather than inventing one.
        """
        flux_unknown = AgronomicDepletionEngine.calculate_crop_removal("Dragonfruit", 8.0, "2024-08-01")
        self.assertTrue(flux_unknown.review_required)
        self.assertTrue(any("FLAG_UNSUPPORTED_CROP_NO_DEFENSIBLE_THRESHOLD" in f for f in flux_unknown.review_flags))
        self.assertTrue(any("No defensible yield threshold exists" in a for a in flux_unknown.assumptions))


class TestTimelineManager(unittest.TestCase):

    def setUp(self):
        self.mgr = PlotTimelineManager(plot_id="PLOT_MAHARASHTRA_101")

    def test_event_chronological_ordering(self):
        """Events added out of chronological order are automatically sorted."""
        self.mgr.record_crop_harvest("Wheat", 3.0, "2025-04-10")
        self.mgr.record_fertilizer_application("Urea", 100.0, "2023-06-20")
        self.mgr.record_crop_harvest("Soybean", 2.0, "2024-10-15")

        event_dates = [e.event_date for e in self.mgr.flux_events]
        self.assertEqual(event_dates, ["2023-06-20", "2024-10-15", "2025-04-10"])

    def test_irregular_multi_year_timeline(self):
        """Handles 2023 baseline, skipped 2024, 2025 activity, 2026 target without annual requirement."""
        # 2023 Lab Test Baseline
        lab_2023 = MeasuredLaboratoryReport(
            report_id="LAB_MH_2023",
            plot_id="PLOT_MAHARASHTRA_101",
            sample_date="2023-05-15",
            lab_name="District Soil Testing Lab, Latur"
        )
        self.mgr.add_lab_report(lab_2023)

        # 2024 has NO lab test, but 1 fertilizer application
        self.mgr.record_fertilizer_application("DAP", 100.0, "2024-06-20")

        # 2025 harvest
        self.mgr.record_crop_harvest("Soybean", 2.5, "2025-10-10")

        # Query mass-balance ledger up to 2026
        ledger = self.mgr.get_mass_balance_ledger(target_date="2026-01-15")

        self.assertEqual(ledger.start_date, "2023-05-15")
        self.assertEqual(ledger.end_date, "2026-01-15")
        # DAP added 18 kg N, Soybean removed 2.5 * 29.25 = 73.125 kg N -> net N = 18 - 73.125 = -55.12 kg N
        self.assertEqual(ledger.gross_n_added_kg_ha, 18.0)
        self.assertAlmostEqual(ledger.gross_n_removed_kg_ha, 73.12, places=1)
        self.assertAlmostEqual(ledger.net_balance_n_kg_ha, -55.12, places=1)

        # Scientific disclaimer must be present
        self.assertIn("CRITICAL SCIENTIFIC DISTINCTION", ledger.disclaimer)

    def test_missing_baseline_abstains(self):
        """Plot without any physical laboratory test report must abstain."""
        mgr_no_lab = PlotTimelineManager(plot_id="PLOT_EMPTY")
        mgr_no_lab.record_fertilizer_application("Urea", 50.0, "2024-06-01")

        assessment = mgr_no_lab.assess_data_sufficiency(target_date="2025-01-01")
        self.assertFalse(assessment.has_baseline_test)
        self.assertFalse(assessment.is_sufficient)
        self.assertIn("No physical laboratory soil test", assessment.abstain_reason)

    def test_outdated_baseline_freshness_warning(self):
        """Baseline > 36 months old with no intervening records triggers warning and abstention."""
        old_lab = MeasuredLaboratoryReport(
            report_id="LAB_OLD_2020",
            plot_id="PLOT_MAHARASHTRA_101",
            sample_date="2020-01-01",
            lab_name="Old Lab"
        )
        self.mgr.add_lab_report(old_lab)

        # Query in 2024 (> 48 months elapsed, zero intervening events)
        assessment = self.mgr.assess_data_sufficiency(target_date="2024-06-01")
        self.assertTrue(assessment.freshness_warning)
        self.assertFalse(assessment.is_sufficient)
        self.assertIn("month threshold", assessment.abstain_reason)


    def test_cumulative_ledger_flags_suspicious_high_yield_events(self):
        """
        D-02: Ledger must flag when harvest events within the window contain unconfirmed
        suspicious yields, preserving numbers without silent clamping.
        """
        lab = MeasuredLaboratoryReport(
            report_id="LAB_TEST_2024",
            plot_id="PLOT_MAHARASHTRA_101",
            sample_date="2024-01-01",
            lab_name="District Lab"
        )
        self.mgr.add_lab_report(lab)

        # Record suspicious wheat yield (20 t/ha > 8.5 t/ha bound)
        self.mgr.record_crop_harvest("Wheat", 20.0, "2024-04-15")

        ledger = self.mgr.get_mass_balance_ledger(target_date="2024-06-01")
        self.assertTrue(ledger.has_unreviewed_suspicious_events)
        self.assertTrue(any("FLAG_UNCONFIRMED_HIGH_YIELD_IN_LEDGER" in f for f in ledger.data_quality_flags))
        self.assertTrue(any("SUSPICIOUS_HIGH_YIELD" in f for f in ledger.data_quality_flags))
        # Gross N removal preserves the verbatim calculation: 20 * 24.5 = 490 kg N
        self.assertEqual(ledger.gross_n_removed_kg_ha, 490.0)


if __name__ == "__main__":
    unittest.main()

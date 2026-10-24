"""
Soil Intelligence Report Builder & ViewModel Assembler
======================================================
Compiles raw timeline, laboratory, mass-balance, and uncertainty data
into a structured, presentation-ready SoilReportViewModel.

Adheres strictly to Phase 6 requirements:
  - Preserves privacy: masks identifiable survey / farmer numbers.
  - Distinguishes verbatim lab readings from converted elemental kg/ha.
  - Explicitly isolates bookkeeping ledgers from soil test concentrations.
  - Highlights review flags, data gaps, and uncalibrated uncertainty limits.
  - Generates clear abstention reasons and actionable retesting advice.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from datetime import datetime
import re

from ml.soil_intelligence.schemas import (
    ProvenanceType,
    NutrientUnit,
    ChemicalForm,
    MeasuredLaboratoryReport,
    ModelledEnvironmentalContext,
    TestMethod
)
from ml.soil_intelligence.timeline.timeline_manager import PlotTimelineManager
from ml.soil_intelligence.model.predictor import (
    SoilIntelligenceReport,
    SoilIntelligencePredictor
)
from ml.soil_intelligence.reporting.advisory import (
    AgronomicAdvisoryEngine,
    SoilAdvisoryBundle
)


@dataclass
class MeasuredParameterRow:
    parameter: str
    reported_reading: str                     # e.g., "18.5 ppm P2O5"
    reported_method: str                      # e.g., "Olsen 0.5M NaHCO3"
    normalized_elemental: str                 # e.g., "16.1 kg/ha P"
    conversion_basis: str                     # e.g., "Depth 0.15m, density 1.33 g/cm3, P2O5 factor 0.4364"
    fertility_tier: str                       # e.g., "Medium (10 - 24.4 kg/ha)"
    provenance: str = "MEASURED"


@dataclass
class ChronologicalEventRow:
    event_date: str
    event_type: str                           # 'CROP_HARVEST', 'FERTILIZER', 'MANURE', 'LAB_TEST'
    description: str
    delta_n_kg_ha: str
    delta_p_kg_ha: str
    delta_k_kg_ha: str
    provenance: str = "FARMER_RECORDED"
    is_suspicious_yield: bool = False
    review_flags: List[str] = field(default_factory=list)


@dataclass
class SoilReportViewModel:
    report_id: str
    generation_date: str
    plot_id_display: str                      # Privacy-protected display identifier
    farm_id_display: str                      # Privacy-protected farm identifier
    location_summary: str                     # e.g., "Latur District, Maharashtra"
    overall_status: str                       # "MEASURED", "INSUFFICIENT_DATA", "ESTIMATED"
    is_prediction_authorized: bool

    # Section 1: Laboratory Baseline Information
    has_lab_baseline: bool
    lab_sample_date: str
    lab_name: str
    lab_certificate_no: str
    lab_accreditation_id: Optional[str]
    accreditation_verified: bool
    accreditation_source: Optional[str]
    accreditation_status_label: str
    lab_review_required: bool
    lab_review_flags: List[str]
    measured_parameters: List[MeasuredParameterRow]

    # Section 2: Chronological Management History
    timeline_events: List[ChronologicalEventRow]

    # Section 3: Separate Mass-Balance Ledger (Bookkeeping ONLY)
    has_mass_balance: bool
    gross_additions: Dict[str, float]
    gross_removals: Dict[str, float]
    net_balance: Dict[str, float]
    balance_uncertainty: Dict[str, float]
    unrecorded_days: int
    data_quality_flags: List[str]

    # Section 4: Environmental Context (REGIONAL_MODEL)
    has_environmental_context: bool
    environmental_data: Dict[str, Any]

    # Section 5: Uncertainty Breakdown (UNCALIBRATED)
    has_uncertainty_breakdown: bool
    uncertainty_bounds: Dict[str, float]
    uncertainty_disclaimer: str

    # Section 6: Prediction Status & Safe Abstention Details
    prediction_status_label: str
    abstain_reasons: List[str]
    missing_evidence: List[str]
    data_requirements_to_unlock: List[str]

    # Section 7: Farmer Advisory & Practical Next Steps
    advisory_bundle: Optional[SoilAdvisoryBundle]
    retesting_advice: List[str]
    retesting_depth_cm: str
    qualified_agronomist_notice: str
    mandatory_scientific_disclaimer: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "report_id": self.report_id,
            "generation_date": self.generation_date,
            "plot_id_display": self.plot_id_display,
            "farm_id_display": self.farm_id_display,
            "overall_status": self.overall_status,
            "is_prediction_authorized": self.is_prediction_authorized,
            "has_lab_baseline": self.has_lab_baseline,
            "lab_sample_date": self.lab_sample_date,
            "lab_name": self.lab_name,
            "measured_parameters": [p.__dict__ for p in self.measured_parameters],
            "timeline_events": [e.__dict__ for e in self.timeline_events],
            "net_balance": self.net_balance,
            "abstain_reasons": self.abstain_reasons,
            "retesting_advice": self.retesting_advice,
        }


class SoilReportBuilder:
    """
    Transforms timeline managers and intelligence reports into privacy-safe,
    verified SoilReportViewModels.
    """

    @staticmethod
    def mask_identifier(ident: Optional[str]) -> str:
        """Applies privacy masking to plot/farm IDs (e.g., PLOT_MH_LAT_881 -> PLOT_MH_LAT_****81)."""
        if not ident or not ident.strip():
            return "UNSPECIFIED_PLOT"
        clean = ident.strip()
        if len(clean) <= 6:
            return clean[:2] + "****" + clean[-1:]
        prefix = clean[:len(clean)-4]
        suffix = clean[-2:]
        if not prefix.endswith("_") and not prefix.endswith("-"):
            return f"{prefix}_****{suffix}"
        return f"{prefix}****{suffix}"

    @classmethod
    def build_view_model(
        cls,
        timeline: PlotTimelineManager,
        intelligence_report: SoilIntelligenceReport
    ) -> SoilReportViewModel:
        """
        Builds the unified SoilReportViewModel adhering to all 10 report sections.
        """
        plot_disp = cls.mask_identifier(timeline.plot_id)
        farm_disp = cls.mask_identifier(timeline.farm_id or "FARM_GENERIC")
        gen_date = datetime.now().strftime("%Y-%m-%d %H:%M UTC")

        baseline = intelligence_report.baseline_measured_report

        # 1. Measured Parameters Table
        measured_rows: List[MeasuredParameterRow] = []
        review_flags = []
        has_lab = baseline is not None

        if baseline:
            if baseline.review_required:
                review_flags.append("FLAG_REVIEW_REQUIRED: Laboratory certificate contains parameters flagged for agronomist review.")
            if baseline.extraction_confidence < 0.90:
                review_flags.append(f"FLAG_LOW_CONFIDENCE: Extraction confidence score is {baseline.extraction_confidence*100:.1f}%.")

            # Nitrogen
            if baseline.nitrogen:
                n_meas = baseline.nitrogen
                n_adv = AgronomicAdvisoryEngine.classify_nitrogen(n_meas.normalized_value_kg_ha, n_meas.reported_value, n_meas.reported_unit.value)
                measured_rows.append(MeasuredParameterRow(
                    parameter="Available Nitrogen (N)",
                    reported_reading=f"{n_meas.reported_value:.1f} {n_meas.reported_unit.value} ({n_meas.reported_form.value})",
                    reported_method=n_meas.test_method.value,
                    normalized_elemental=f"{n_meas.normalized_value_kg_ha:.1f} kg/ha elemental N",
                    conversion_basis=n_meas.conversion_applied,
                    fertility_tier=n_adv.status_label,
                    provenance="MEASURED"
                ))

            # Phosphorus
            if baseline.phosphorus:
                p_meas = baseline.phosphorus
                p_adv = AgronomicAdvisoryEngine.classify_phosphorus(p_meas.normalized_value_kg_ha, p_meas.reported_value, p_meas.reported_unit.value)
                measured_rows.append(MeasuredParameterRow(
                    parameter="Available Phosphorus (P)",
                    reported_reading=f"{p_meas.reported_value:.1f} {p_meas.reported_unit.value} ({p_meas.reported_form.value})",
                    reported_method=p_meas.test_method.value,
                    normalized_elemental=f"{p_meas.normalized_value_kg_ha:.1f} kg/ha elemental P",
                    conversion_basis=p_meas.conversion_applied,
                    fertility_tier=p_adv.status_label,
                    provenance="MEASURED"
                ))

            # Potassium
            if baseline.potassium:
                k_meas = baseline.potassium
                k_adv = AgronomicAdvisoryEngine.classify_potassium(k_meas.normalized_value_kg_ha, k_meas.reported_value, k_meas.reported_unit.value)
                measured_rows.append(MeasuredParameterRow(
                    parameter="Available Potassium (K)",
                    reported_reading=f"{k_meas.reported_value:.1f} {k_meas.reported_unit.value} ({k_meas.reported_form.value})",
                    reported_method=k_meas.test_method.value,
                    normalized_elemental=f"{k_meas.normalized_value_kg_ha:.1f} kg/ha elemental K",
                    conversion_basis=k_meas.conversion_applied,
                    fertility_tier=k_adv.status_label,
                    provenance="MEASURED"
                ))

            # Soil Reaction pH
            if baseline.ph is not None:
                ph_adv = AgronomicAdvisoryEngine.classify_ph(baseline.ph)
                measured_rows.append(MeasuredParameterRow(
                    parameter="Soil Reaction (pH)",
                    reported_reading=f"{baseline.ph:.2f} pH",
                    reported_method="Potentiometric 1:2.5 suspension",
                    normalized_elemental=f"{baseline.ph:.2f} pH scale",
                    conversion_basis="Direct standard scale",
                    fertility_tier=ph_adv.status_label if ph_adv else "Normal",
                    provenance="MEASURED"
                ))

            # Electrical Conductivity
            if baseline.ec_ds_m is not None:
                measured_rows.append(MeasuredParameterRow(
                    parameter="Electrical Conductivity (EC)",
                    reported_reading=f"{baseline.ec_ds_m:.2f} dS/m",
                    reported_method="Conductivity bridge 1:2.5 suspension",
                    normalized_elemental=f"{baseline.ec_ds_m:.2f} dS/m",
                    conversion_basis="Direct standard scale",
                    fertility_tier="Normal (< 1.0 dS/m)" if baseline.ec_ds_m < 1.0 else "Critical",
                    provenance="MEASURED"
                ))

            # Organic Carbon
            if baseline.organic_carbon_pct is not None:
                oc = baseline.organic_carbon_pct
                tier_str = "Low (< 0.5%)" if oc < 0.50 else ("Medium (0.5 - 0.75%)" if oc <= 0.75 else "High (> 0.75%)")
                measured_rows.append(MeasuredParameterRow(
                    parameter="Organic Carbon (OC)",
                    reported_reading=f"{oc:.2f} %",
                    reported_method="Walkley-Black wet oxidation",
                    normalized_elemental=f"{oc:.2f} % by weight",
                    conversion_basis="Direct gravimetric fraction",
                    fertility_tier=tier_str,
                    provenance="MEASURED"
                ))

        # 2. Chronological Timeline Events
        chron_events: List[ChronologicalEventRow] = []
        for fe in timeline.flux_events:
            is_susp = getattr(fe, 'review_required', False)
            flags_ev = list(getattr(fe, 'review_flags', []))
            desc = fe.description
            if is_susp:
                desc += " [SUSPICIOUS HIGH YIELD - REVIEW REQUIRED]"
            chron_events.append(ChronologicalEventRow(
                event_date=fe.event_date,
                event_type=fe.event_type,
                description=desc,
                delta_n_kg_ha=f"{fe.delta_n_kg_ha:+.1f} kg N",
                delta_p_kg_ha=f"{fe.delta_p_elemental_kg_ha:+.1f} kg P",
                delta_k_kg_ha=f"{fe.delta_k_elemental_kg_ha:+.1f} kg K",
                provenance=fe.provenance.value,
                is_suspicious_yield=is_susp,
                review_flags=flags_ev
            ))

        # 3. Mass-Balance Ledger Data
        ledger = intelligence_report.mass_balance_ledger
        has_ledger = ledger is not None
        gross_add = {
            "N": ledger.gross_n_added_kg_ha if has_ledger else 0.0,
            "P": ledger.gross_p_added_kg_ha if has_ledger else 0.0,
            "K": ledger.gross_k_added_kg_ha if has_ledger else 0.0,
        }
        gross_rem = {
            "N": ledger.gross_n_removed_kg_ha if has_ledger else 0.0,
            "P": ledger.gross_p_removed_kg_ha if has_ledger else 0.0,
            "K": ledger.gross_k_removed_kg_ha if has_ledger else 0.0,
        }
        net_bal = {
            "N": ledger.net_balance_n_kg_ha if has_ledger else 0.0,
            "P": ledger.net_balance_p_kg_ha if has_ledger else 0.0,
            "K": ledger.net_balance_k_kg_ha if has_ledger else 0.0,
        }
        bal_unc = {
            "N": ledger.balance_uncertainty_n_kg_ha if has_ledger else 0.0,
            "P": ledger.balance_uncertainty_p_kg_ha if has_ledger else 0.0,
            "K": ledger.balance_uncertainty_k_kg_ha if has_ledger else 0.0,
        }
        unrec_days = ledger.unrecorded_days_estimate if has_ledger else 0
        ledger_flags = list(ledger.data_quality_flags) if has_ledger else []

        # 4. Environmental Context
        env = intelligence_report.environmental_context
        has_env = env is not None
        env_dict = {
            "sand_fraction_pct": env.sand_fraction_pct if has_env else None,
            "silt_fraction_pct": env.silt_fraction_pct if has_env else None,
            "clay_fraction_pct": env.clay_fraction_pct if has_env else None,
            "bulk_density_g_cm3": env.bulk_density_g_cm3 if has_env else None,
            "disclaimer": env.disclaimer if has_env else None,
            "provenance": "REGIONAL_MODEL"
        }

        # 5. Uncertainty Breakdown
        unc = intelligence_report.uncertainty_breakdown
        has_unc = unc is not None
        unc_bounds = {
            "N": unc.nitrogen_uncertainty.total_composite_bound_kg_ha if has_unc else 0.0,
            "P": unc.phosphorus_uncertainty.total_composite_bound_kg_ha if has_unc else 0.0,
            "K": unc.potassium_uncertainty.total_composite_bound_kg_ha if has_unc else 0.0,
        }

        # 6. Abstention & Prediction Status
        pred_label = "INSUFFICIENT_DATA (Operational Empirical Prediction Gated)"
        abstain_reasons = []
        missing_evidence = []
        if intelligence_report.abstention_decision:
            abst = intelligence_report.abstention_decision
            abstain_reasons = list(abst.detailed_reasons)
            missing_evidence = list(abst.missing_evidence)

        # 7. Advisory Bundle
        advisory_bundle = None
        if baseline:
            advisory_bundle = AgronomicAdvisoryEngine.generate_plot_advisory_bundle(
                plot_id=timeline.plot_id,
                n_kg_ha=baseline.nitrogen.normalized_value_kg_ha if baseline.nitrogen else None,
                p_kg_ha=baseline.phosphorus.normalized_value_kg_ha if baseline.phosphorus else None,
                k_kg_ha=baseline.potassium.normalized_value_kg_ha if baseline.potassium else None,
                ph=baseline.ph,
                ec_ds_m=baseline.ec_ds_m,
                oc_pct=baseline.organic_carbon_pct
            )

        retest_advice = list(intelligence_report.actionable_recommendations)
        if not retest_advice:
            retest_advice = ["Maintain routine annual crop and fertilizer application logging."]

        # D-01: Laboratory certification status handling
        # A populated laboratory name, certificate field, or accreditation ID alone must NOT establish verified status.
        # Only an explicitly verified record (accreditation_verified is True) grants verified status.
        acc_verified = False
        acc_label = "NO_LAB_BASELINE"
        acc_id = None
        acc_source = None
        if baseline:
            acc_id = getattr(baseline, 'lab_accreditation_id', None)
            acc_source = getattr(baseline, 'accreditation_source', None)
            if getattr(baseline, 'accreditation_verified', False) is True:
                acc_verified = True
                acc_label = f"VERIFIED ACCREDITED ({acc_source or 'Official Registry'})"
            elif acc_id or baseline.lab_certificate_no:
                acc_verified = False
                acc_label = "UNVERIFIED SELF-REPORTED CREDENTIALS (Verification Pending)"
            else:
                acc_verified = False
                acc_label = "UNVERIFIED / NO ACCREDITATION DATA"

        return SoilReportViewModel(
            report_id=intelligence_report.report_id,
            generation_date=gen_date,
            plot_id_display=plot_disp,
            farm_id_display=farm_disp,
            location_summary="Latur District / Marathwada Region, Maharashtra",
            overall_status=intelligence_report.overall_status.value,
            is_prediction_authorized=intelligence_report.is_operational_authorized,
            has_lab_baseline=has_lab,
            lab_sample_date=baseline.sample_date if baseline else "No Lab Test On Record",
            lab_name=baseline.lab_name if baseline else "None",
            lab_certificate_no=baseline.lab_certificate_no or "None" if baseline else "None",
            lab_accreditation_id=acc_id,
            accreditation_verified=acc_verified,
            accreditation_source=acc_source,
            accreditation_status_label=acc_label,
            lab_review_required=baseline.review_required if baseline else False,
            lab_review_flags=review_flags,
            measured_parameters=measured_rows,
            timeline_events=chron_events,
            has_mass_balance=has_ledger,
            gross_additions=gross_add,
            gross_removals=gross_rem,
            net_balance=net_bal,
            balance_uncertainty=bal_unc,
            unrecorded_days=unrec_days,
            data_quality_flags=ledger_flags,
            has_environmental_context=has_env,
            environmental_data=env_dict,
            has_uncertainty_breakdown=has_unc,
            uncertainty_bounds=unc_bounds,
            uncertainty_disclaimer=(
                "UNCALIBRATED HEURISTIC BOUNDS: Uncertainty values are computed using published ICAR "
                "literature variance and time drift propagation. They are strictly UNCALIBRATED bounds "
                "and MUST NOT be interpreted as empirical prediction intervals or confidence intervals."
            ),
            prediction_status_label=pred_label,
            abstain_reasons=abstain_reasons,
            missing_evidence=missing_evidence,
            data_requirements_to_unlock=[
                "Accredited longitudinal dataset with repeated soil measurements on identical plot boundaries across seasons.",
                "Leakage-safe GroupedKFold holdout validation demonstrating >= 80% accuracy within approved nutrient tolerances.",
                "Officially ratified agronomic error tolerances signed off by a recognized university/ICAR panel."
            ],
            advisory_bundle=advisory_bundle,
            retesting_advice=retest_advice,
            retesting_depth_cm="0 - 15 cm (standard topsoil plow layer)",
            qualified_agronomist_notice=(
                "IMPORTANT: For site-specific fertilizer scheduling and crop guidance, always consult a "
                "certified agronomist at your local Krishi Vigyan Kendra (KVK) or State Agricultural University."
            ),
            mandatory_scientific_disclaimer=intelligence_report.scientific_disclaimer
        )

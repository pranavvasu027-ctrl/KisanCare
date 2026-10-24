"""
Soil Intelligence Prediction Engine & Orchestrator
==================================================
Orchestrates dynamic soil intelligence while strictly maintaining scientific integrity:
  1. Input verification: lab baseline provenance, units, methods, and management completeness.
  2. Distinct output types: MEASURED, ESTIMATED, REGIONAL_MODEL, FARMER_RECORDED, INSUFFICIENT_DATA.
  3. Safe abstention: returns INSUFFICIENT_DATA whenever ground truth, baseline, or timeline is inadequate.
  4. Mass-balance separation: nutrient balance ledger is strictly bookkeeping; NEVER converted
     directly into extractable soil test NPK.
  5. Uncertainty decomposition: uncalibrated physical bounds explicitly separated from calibrated claims.
  6. Operational Gate: respects ModelValidationGate; blocks operational empirical claims until genuine
     longitudinal ground truth is available.
"""

from dataclasses import dataclass, field, asdict
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime
import uuid

from ml.soil_intelligence.schemas import (
    ProvenanceType,
    NutrientUnit,
    ChemicalForm,
    NutrientMeasurement,
    MeasuredLaboratoryReport,
    ModelledEnvironmentalContext,
    NutrientPrediction,
    SoilPredictionRecord,
    AgronomicTolerances
)
from ml.soil_intelligence.timeline.timeline_manager import (
    PlotTimelineManager,
    TimelineSufficiencyAssessment
)
from ml.soil_intelligence.timeline.agronomic_depletion import (
    CumulativeMassBalanceLedger,
    AgronomicDepletionEngine
)
from ml.soil_intelligence.model.validation_gate import (
    ModelValidationGate,
    ValidationGateDecision,
    ModelValidationScope,
    ValidationEvidenceBundle
)
from ml.soil_intelligence.model.uncertainty import (
    UncertaintyEngine,
    SoilUncertaintyBreakdown,
    CalibrationStatus
)
from ml.soil_intelligence.model.abstention import (
    AbstentionEngine,
    AbstentionDecision,
    AbstentionReasonCode,
    RetestingUrgency
)


MODEL_VERSION: str = "KISANcare-SoilIntel-V1.0-Uncalibrated"


@dataclass
class SoilIntelligenceReport:
    """
    Unified, structured report representing the complete soil intelligence state for a plot.
    Guarantees strict separation between physical lab measurements, farmer-recorded fluxes,
    regional environmental context, and algorithmic estimates.
    """
    report_id: str
    plot_id: str
    farm_id: Optional[str]
    target_date: str
    overall_status: ProvenanceType
    model_version: str
    is_operational_authorized: bool
    validation_scope: ModelValidationScope

    # 1. Measured Physical Laboratory Baseline (MEASURED)
    baseline_measured_report: Optional[MeasuredLaboratoryReport] = None
    baseline_sample_date: Optional[str] = None
    months_since_baseline: Optional[float] = None

    # 2. Agronomic Nutrient Mass-Balance Ledger (FARMER_RECORDED Bookkeeping ONLY)
    mass_balance_ledger: Optional[CumulativeMassBalanceLedger] = None

    # 3. Auxiliary Regional Environmental Raster Context (REGIONAL_MODEL)
    environmental_context: Optional[ModelledEnvironmentalContext] = None

    # 4. Uncertainty Decomposition Breakdown (UNCALIBRATED)
    uncertainty_breakdown: Optional[SoilUncertaintyBreakdown] = None

    # 5. Model Prediction Record (ESTIMATED or INSUFFICIENT_DATA)
    prediction_record: Optional[SoilPredictionRecord] = None

    # 6. Safe Abstention Details (if abstained)
    abstention_decision: Optional[AbstentionDecision] = None

    # 7. Actionable Retesting & Agronomic Advice
    actionable_recommendations: List[str] = field(default_factory=list)
    limitations: List[str] = field(default_factory=list)
    scientific_disclaimer: str = (
        "SCIENTIFIC HONESTY MANDATE: Nutrient mass-balance additions minus removals represent "
        "a field-scale bookkeeping ledger only. They DO NOT equal extractable available soil test NPK "
        "(e.g., Alkaline KMnO4 N, Olsen P, NH4OAc K). No calibrated longitudinal empirical prediction "
        "model is authorized until validated against independent, accredited ground truth."
    )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "report_id": self.report_id,
            "plot_id": self.plot_id,
            "farm_id": self.farm_id,
            "target_date": self.target_date,
            "overall_status": self.overall_status.value,
            "model_version": self.model_version,
            "is_operational_authorized": self.is_operational_authorized,
            "validation_scope": self.validation_scope.value,
            "baseline_measured_report": self.baseline_measured_report.to_dict() if self.baseline_measured_report else None,
            "baseline_sample_date": self.baseline_sample_date,
            "months_since_baseline": self.months_since_baseline,
            "mass_balance_ledger": self.mass_balance_ledger.to_dict() if self.mass_balance_ledger else None,
            "environmental_context": self.environmental_context.to_dict() if self.environmental_context else None,
            "uncertainty_breakdown": self.uncertainty_breakdown.to_dict() if self.uncertainty_breakdown else None,
            "prediction_record": self.prediction_record.to_dict() if self.prediction_record else None,
            "abstention_decision": self.abstention_decision.to_dict() if self.abstention_decision else None,
            "actionable_recommendations": self.actionable_recommendations,
            "limitations": self.limitations,
            "scientific_disclaimer": self.scientific_disclaimer,
        }


class SoilIntelligencePredictor:
    """
    Orchestrates soil intelligence predictions with mandatory validation gating,
    transparent uncertainty, and safe abstention.
    """

    def __init__(
        self,
        evidence_bundle: Optional[ValidationEvidenceBundle] = None,
        longitudinal_ground_truth_available: bool = False,
        cross_sectional_data_available: bool = True,
        is_synthetic_data: bool = False,
        independent_holdout_evaluated: bool = False,
        tolerance_target_met: bool = False,
        version: str = MODEL_VERSION
    ):
        self.version = version
        self.evidence_bundle = evidence_bundle
        self.longitudinal_available = (evidence_bundle is not None and not evidence_bundle.dataset_audit.is_synthetic)
        self.cross_sectional_available = cross_sectional_data_available
        self.is_synthetic = is_synthetic_data
        self.independent_holdout_evaluated = (evidence_bundle is not None)
        self.tolerance_target_met = (evidence_bundle is not None)

        # Evaluate validation gate at instantiation strictly requiring verified evidence bundle
        self.gate_decision = ModelValidationGate.evaluate_task(
            task_name="OPERATIONAL_ESTIMATE",
            evidence_bundle=evidence_bundle,
            cross_sectional_data_available=cross_sectional_data_available,
            is_synthetic_data=is_synthetic_data,
            longitudinal_data_available=longitudinal_ground_truth_available,
            independent_holdout_evaluated=independent_holdout_evaluated,
            tolerance_target_met=tolerance_target_met
        )

    def evaluate_plot(
        self,
        timeline: PlotTimelineManager,
        target_date: str,
        allow_unvalidated_research: bool = False
    ) -> SoilIntelligenceReport:
        """
        Evaluates a plot's multi-year timeline up to the target date.
        If operational prediction is blocked or evidence is insufficient, returns
        a structured INSUFFICIENT_DATA report with verified lab baseline, ledger,
        uncertainty bounds, and actionable recommendations.
        """
        report_id = f"SIR_{timeline.plot_id}_{target_date}_{uuid.uuid4().hex[:8]}"

        # 1. Timeline sufficiency assessment
        sufficiency = timeline.assess_data_sufficiency(target_date)
        baseline = timeline.get_latest_baseline_report(target_date)

        # 2. Retrieve mass-balance ledger (bookkeeping only)
        ledger = timeline.get_mass_balance_ledger(target_date)

        # 3. Calculate uncalibrated uncertainty breakdown
        base_n = baseline.nitrogen.normalized_value_kg_ha if (baseline and baseline.nitrogen) else None
        base_p = baseline.phosphorus.normalized_value_kg_ha if (baseline and baseline.phosphorus) else None
        base_k = baseline.potassium.normalized_value_kg_ha if (baseline and baseline.potassium) else None

        has_unverified_proxies = any(
            any("proxy" in a.lower() for a in getattr(e, "assumptions", []))
            for e in timeline.flux_events
        )

        uncertainty_breakdown = UncertaintyEngine.decompose_uncertainty(
            plot_id=timeline.plot_id,
            target_date=target_date,
            baseline_n_kg_ha=base_n,
            baseline_p_kg_ha=base_p,
            baseline_k_kg_ha=base_k,
            ledger_unc_n=ledger.balance_uncertainty_n_kg_ha if ledger else 0.0,
            ledger_unc_p=ledger.balance_uncertainty_p_kg_ha if ledger else 0.0,
            ledger_unc_k=ledger.balance_uncertainty_k_kg_ha if ledger else 0.0,
            unrecorded_gap_days=sufficiency.unrecorded_gap_days,
            months_since_baseline=sufficiency.months_since_baseline or 0.0,
            has_unverified_proxies=has_unverified_proxies
        )

        # 4. Evaluate Abstention Engine
        intervening_count = len([
            e for e in timeline.flux_events
            if (baseline and baseline.sample_date < e.event_date <= target_date)
        ])

        abstention = AbstentionEngine.evaluate(
            plot_id=timeline.plot_id,
            target_date=target_date,
            baseline_report=baseline,
            months_since_baseline=sufficiency.months_since_baseline,
            coverage_score=sufficiency.coverage_score,
            unrecorded_gap_days=sufficiency.unrecorded_gap_days,
            intervening_events_count=intervening_count,
            validation_decision=self.gate_decision,
            allow_unvalidated_research=allow_unvalidated_research
        )

        limitations = [
            "Cumulative nutrient flux is a mass-balance accounting ledger, NOT extractable soil test available NPK.",
            "Soil biological mineralization, clay potassium fixation, and phosphate sorption require empirical calibration.",
            "All uncertainty bounds are heuristic engineering bounds; they are not empirically calibrated prediction intervals."
        ]

        # Case A: Abstention mandated (insufficient data, unverified plot, expired timeline, or operational gate blocked)
        if abstention.should_abstain:
            pred_record = SoilPredictionRecord(
                prediction_id=f"PRED_{timeline.plot_id}_{target_date}",
                plot_id=timeline.plot_id,
                prediction_date=target_date,
                model_version=self.version,
                status=ProvenanceType.INSUFFICIENT_DATA,
                nitrogen=None,
                phosphorus=None,
                potassium=None,
                input_data_coverage_score=sufficiency.coverage_score,
                has_valid_baseline=(baseline is not None),
                months_since_last_test=sufficiency.months_since_baseline,
                abstain_reason=abstention.primary_reason,
                retesting_advice="; ".join(abstention.actionable_recommendations)
            )

            return SoilIntelligenceReport(
                report_id=report_id,
                plot_id=timeline.plot_id,
                farm_id=timeline.farm_id,
                target_date=target_date,
                overall_status=ProvenanceType.INSUFFICIENT_DATA,
                model_version=self.version,
                is_operational_authorized=self.gate_decision.is_authorized_for_operational_prediction,
                validation_scope=self.gate_decision.scope,
                baseline_measured_report=baseline,
                baseline_sample_date=baseline.sample_date if baseline else None,
                months_since_baseline=sufficiency.months_since_baseline,
                mass_balance_ledger=ledger,
                environmental_context=timeline.environmental_context,
                uncertainty_breakdown=uncertainty_breakdown,
                prediction_record=pred_record,
                abstention_decision=abstention,
                actionable_recommendations=abstention.actionable_recommendations,
                limitations=limitations
            )

        # Case B: Only reached if validation gate permits operational prediction AND timeline is sufficient
        # (Reserved for when accredited longitudinal ground truth is unlocked)
        pred_record = SoilPredictionRecord(
            prediction_id=f"PRED_{timeline.plot_id}_{target_date}",
            plot_id=timeline.plot_id,
            prediction_date=target_date,
            model_version=self.version,
            status=ProvenanceType.ESTIMATED,
            nitrogen=NutrientPrediction(
                nutrient="N",
                predicted_kg_ha=round(base_n, 2) if base_n else 0.0,
                uncertainty_lower_kg_ha=round(max(0.0, base_n - uncertainty_breakdown.nitrogen_uncertainty.total_composite_bound_kg_ha), 2) if base_n else 0.0,
                uncertainty_upper_kg_ha=round((base_n or 0.0) + uncertainty_breakdown.nitrogen_uncertainty.total_composite_bound_kg_ha, 2),
                status=ProvenanceType.ESTIMATED,
                baseline_used_id=baseline.report_id if baseline else None,
                days_since_baseline=int((sufficiency.months_since_baseline or 0) * 30.4)
            ),
            phosphorus=NutrientPrediction(
                nutrient="P",
                predicted_kg_ha=round(base_p, 2) if base_p else 0.0,
                uncertainty_lower_kg_ha=round(max(0.0, base_p - uncertainty_breakdown.phosphorus_uncertainty.total_composite_bound_kg_ha), 2) if base_p else 0.0,
                uncertainty_upper_kg_ha=round((base_p or 0.0) + uncertainty_breakdown.phosphorus_uncertainty.total_composite_bound_kg_ha, 2),
                status=ProvenanceType.ESTIMATED,
                baseline_used_id=baseline.report_id if baseline else None,
                days_since_baseline=int((sufficiency.months_since_baseline or 0) * 30.4)
            ),
            potassium=NutrientPrediction(
                nutrient="K",
                predicted_kg_ha=round(base_k, 2) if base_k else 0.0,
                uncertainty_lower_kg_ha=round(max(0.0, base_k - uncertainty_breakdown.potassium_uncertainty.total_composite_bound_kg_ha), 2) if base_k else 0.0,
                uncertainty_upper_kg_ha=round((base_k or 0.0) + uncertainty_breakdown.potassium_uncertainty.total_composite_bound_kg_ha, 2),
                status=ProvenanceType.ESTIMATED,
                baseline_used_id=baseline.report_id if baseline else None,
                days_since_baseline=int((sufficiency.months_since_baseline or 0) * 30.4)
            ),
            input_data_coverage_score=sufficiency.coverage_score,
            has_valid_baseline=True,
            months_since_last_test=sufficiency.months_since_baseline,
            abstain_reason=None,
            retesting_advice="Routine testing recommended within 36 months."
        )

        return SoilIntelligenceReport(
            report_id=report_id,
            plot_id=timeline.plot_id,
            farm_id=timeline.farm_id,
            target_date=target_date,
            overall_status=ProvenanceType.ESTIMATED,
            model_version=self.version,
            is_operational_authorized=True,
            validation_scope=ModelValidationScope.VALIDATED_FOR_SCOPE,
            baseline_measured_report=baseline,
            baseline_sample_date=baseline.sample_date if baseline else None,
            months_since_baseline=sufficiency.months_since_baseline,
            mass_balance_ledger=ledger,
            environmental_context=timeline.environmental_context,
            uncertainty_breakdown=uncertainty_breakdown,
            prediction_record=pred_record,
            abstention_decision=abstention,
            actionable_recommendations=["Maintain routine crop and fertilizer logging."],
            limitations=limitations
        )

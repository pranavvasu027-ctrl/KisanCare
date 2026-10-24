"""
KISANcare Soil Intelligence V1 - Leakage-Safe Model Evaluation Engine
=====================================================================
Evaluates batches of historical prediction vs. ground-truth comparisons
across Nitrogen (N), Phosphorus (P), and Potassium (K) to assess performance
against the 80% tolerance release gate.

Scientific & Integrity Safeguards:
  1. Leakage-Safe Splitting: Evaluated strictly under GROUPED_PLOT_TIME_SERIES
     holdouts. Random / stratified train-test splits are rejected for leakage.
  2. Independent Nutrient Evaluation: Metrics (MAE, RMSE, pass-rate) are computed
     separately per nutrient. High Nitrogen accuracy never conceals failing Phosphorus.
  3. Absolute Rejection of Synthetic Data: Evaluation on synthetic or randomly
     perturbed data is strictly blocked.
  4. 80% Target Gate Enforcement: Unless authenticated longitudinal ground truth
     AND ratified agronomic tolerances are present, status remains NOT_YET_VALIDATED.
"""

from typing import Dict, List, Optional, Any
from datetime import datetime
import math
import uuid

from ml.soil_intelligence.schemas import (
    EvaluationTargetStatus,
    ToleranceReviewStatus,
    AgronomicTolerances,
    SingleNutrientComparison,
    EvaluationComparisonRecord,
    NutrientEvaluationSummary,
    ComprehensiveEvaluationReport
)


class SoilIntelligenceEvaluator:
    """
    Evaluates batches of prediction-to-actual comparisons against predefined
    agronomic tolerances and enforces the 80% accuracy validation gate.
    """

    TARGET_TOLERANCE_PASS_RATE_PCT = 80.0
    AUTHORIZED_SPLIT_STRATEGY = "GROUPED_PLOT_TIME_SERIES"

    @classmethod
    def evaluate_comparisons(
        cls,
        records: List[EvaluationComparisonRecord],
        split_strategy: str = AUTHORIZED_SPLIT_STRATEGY,
        model_version: str = "soil-intelligence-v1.0.0",
        data_readiness_passed: bool = False,
        is_synthetic_data: bool = False,
        evaluation_id: Optional[str] = None
    ) -> ComprehensiveEvaluationReport:
        """
        Computes formal evaluation metrics (MAE, RMSE, within-tolerance rate)
        across N, P, and K. Enforces release gate rules.
        """
        # 1. Absolute Rejection of Synthetic Data
        if is_synthetic_data:
            raise ValueError(
                "CRITICAL DATA INTEGRITY VIOLATION: Evaluation on synthetic data is strictly "
                "prohibited. Synthetic data cannot be used to evaluate tolerances or claim accuracy."
            )

        # 2. Leakage-Safe Split Validation
        is_valid_split = (split_strategy == cls.AUTHORIZED_SPLIT_STRATEGY)

        # 3. Evaluate Nitrogen
        n_summary = cls._evaluate_single_nutrient(
            nutrient_name="Nitrogen",
            attr_name="nitrogen_comparison",
            records=records,
            data_readiness_passed=data_readiness_passed,
            is_valid_split=is_valid_split
        )

        # 4. Evaluate Phosphorus
        p_summary = cls._evaluate_single_nutrient(
            nutrient_name="Phosphorus",
            attr_name="phosphorus_comparison",
            records=records,
            data_readiness_passed=data_readiness_passed,
            is_valid_split=is_valid_split
        )

        # 5. Evaluate Potassium
        k_summary = cls._evaluate_single_nutrient(
            nutrient_name="Potassium",
            attr_name="potassium_comparison",
            records=records,
            data_readiness_passed=data_readiness_passed,
            is_valid_split=is_valid_split
        )

        # 6. Overall Gate Status: NEVER conceal one nutrient's failure behind another
        summaries = [n_summary, p_summary, k_summary]

        if any(s.target_status == EvaluationTargetStatus.NOT_MET for s in summaries):
            overall_status = EvaluationTargetStatus.NOT_MET
        elif all(s.target_status == EvaluationTargetStatus.MET for s in summaries):
            overall_status = EvaluationTargetStatus.MET
        else:
            overall_status = EvaluationTargetStatus.NOT_YET_VALIDATED

        eid = evaluation_id or f"EVAL_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:6]}"

        return ComprehensiveEvaluationReport(
            evaluation_id=eid,
            model_version=model_version,
            evaluation_date=datetime.utcnow().strftime("%Y-%m-%d"),
            split_strategy=split_strategy,
            nitrogen_summary=n_summary,
            phosphorus_summary=p_summary,
            potassium_summary=k_summary,
            overall_gate_status=overall_status,
            data_provenance_verified=data_readiness_passed and not is_synthetic_data,
            data_readiness_status="PASSED" if data_readiness_passed else "BLOCKED_PENDING_LONGITUDINAL_GROUND_TRUTH"
        )

    @classmethod
    def _evaluate_single_nutrient(
        cls,
        nutrient_name: str,
        attr_name: str,
        records: List[EvaluationComparisonRecord],
        data_readiness_passed: bool,
        is_valid_split: bool
    ) -> NutrientEvaluationSummary:
        """
        Calculates MAE, RMSE, and within-tolerance rate for an individual nutrient.
        """
        comparisons: List[SingleNutrientComparison] = []
        for r in records:
            comp = getattr(r, attr_name, None)
            if comp is not None:
                comparisons.append(comp)

        tol = AgronomicTolerances.get_tolerance(nutrient_name)
        tol_desc = (
            f"±{tol.absolute_tolerance:.1f} kg/ha or ±{tol.relative_tolerance_pct:.0f}% "
            f"({tol.status.value})"
        )

        if not comparisons:
            return NutrientEvaluationSummary(
                nutrient=nutrient_name,
                sample_count=0,
                mae=0.0,
                rmse=0.0,
                within_tolerance_count=0,
                within_tolerance_rate_pct=0.0,
                target_tolerance_rate_pct=cls.TARGET_TOLERANCE_PASS_RATE_PCT,
                target_status=EvaluationTargetStatus.NOT_YET_VALIDATED,
                tolerance_definition=tol_desc,
                status_explanation="No paired ground-truth samples available for evaluation."
            )

        n = len(comparisons)
        abs_errors = [c.absolute_error_kg_ha for c in comparisons]
        squared_errors = [c.absolute_error_kg_ha ** 2 for c in comparisons]
        within_count = sum(1 for c in comparisons if c.within_tolerance)

        mae = round(sum(abs_errors) / n, 2)
        rmse = round(math.sqrt(sum(squared_errors) / n), 2)
        pass_rate = round((within_count / n) * 100.0, 2)

        # Gate status determination
        # 1. Split strategy must be leakage-safe
        if not is_valid_split:
            status = EvaluationTargetStatus.NOT_YET_VALIDATED
            explanation = (
                f"REJECTED: Split strategy is not '{cls.AUTHORIZED_SPLIT_STRATEGY}'. "
                "Random or un-grouped splits introduce severe spatial leakage and cannot validate accuracy."
            )
        # 2. Ground-truth data readiness gate must be passed
        elif not data_readiness_passed:
            status = EvaluationTargetStatus.NOT_YET_VALIDATED
            explanation = (
                f"Evaluation achieved {pass_rate:.1f}% within tolerance (MAE {mae} kg/ha), but status "
                "remains NOT_YET_VALIDATED because genuine longitudinal ground-truth gate is BLOCKED."
            )
        # 3. Tolerances must not be provisional
        elif tol.status == ToleranceReviewStatus.PROVISIONAL_PENDING_EXPERT_APPROVAL:
            status = EvaluationTargetStatus.NOT_YET_VALIDATED
            explanation = (
                f"Evaluation achieved {pass_rate:.1f}% within tolerance (MAE {mae} kg/ha), but status "
                "remains NOT_YET_VALIDATED because tolerances are PROVISIONAL_PENDING_EXPERT_APPROVAL."
            )
        # 4. Check 80% tolerance threshold
        elif pass_rate >= cls.TARGET_TOLERANCE_PASS_RATE_PCT:
            status = EvaluationTargetStatus.MET
            explanation = (
                f"Target MET: {pass_rate:.1f}% of evaluated plots fall within ratified agronomic tolerance "
                f"(exceeds >= {cls.TARGET_TOLERANCE_PASS_RATE_PCT:.0f}% threshold; MAE {mae} kg/ha, RMSE {rmse} kg/ha)."
            )
        else:
            status = EvaluationTargetStatus.NOT_MET
            explanation = (
                f"Target NOT MET: Only {pass_rate:.1f}% of evaluated plots fall within agronomic tolerance "
                f"(below {cls.TARGET_TOLERANCE_PASS_RATE_PCT:.0f}% target; MAE {mae} kg/ha, RMSE {rmse} kg/ha)."
            )

        return NutrientEvaluationSummary(
            nutrient=nutrient_name,
            sample_count=n,
            mae=mae,
            rmse=rmse,
            within_tolerance_count=within_count,
            within_tolerance_rate_pct=pass_rate,
            target_tolerance_rate_pct=cls.TARGET_TOLERANCE_PASS_RATE_PCT,
            target_status=status,
            tolerance_definition=tol_desc,
            status_explanation=explanation
        )

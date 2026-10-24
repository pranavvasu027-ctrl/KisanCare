"""
Model Validation Gate & Operational Authorization
=================================================
Enforces scientific gates on predictive modeling tasks:
  1. BLOCKED: Insufficient genuine ground truth available or unverified evidence.
  2. RESEARCH_ONLY: Permitted for offline exploratory analysis (e.g. cross-sectional
     SHC baseline distribution), but NOT authorized for operational farm predictions.
  3. VALIDATED_FOR_SCOPE: Formally validated against independent, accredited
     longitudinal ground truth with documented acceptance criteria.

STRICT RULE: VALIDATED_FOR_SCOPE cannot be granted simply by passing loose boolean flags
or manually asserting a status. It strictly requires a verified ValidationEvidenceBundle
containing an accredited DatasetAuditReport, leak-safe ComprehensiveEvaluationReport,
and officially ratified agronomic tolerances.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Any
import hashlib

from ml.soil_intelligence.schemas import (
    ComprehensiveEvaluationReport,
    ToleranceReviewStatus,
    EvaluationTargetStatus,
    NutrientEvaluationSummary
)
from ml.soil_intelligence.data_readiness import (
    DatasetAuditReport,
    GateStatus,
    SamplingDesign
)


class ModelValidationScope(str, Enum):
    BLOCKED = "BLOCKED"
    RESEARCH_ONLY = "RESEARCH_ONLY"
    VALIDATED_FOR_SCOPE = "VALIDATED_FOR_SCOPE"


@dataclass
class ValidationEvidenceBundle:
    """
    Formal, verifiable evidence bundle required to authorize VALIDATED_FOR_SCOPE.
    Prevents bypassing the gate via loose boolean flags or unverified assertions.
    """
    dataset_audit: DatasetAuditReport
    evaluation_report: ComprehensiveEvaluationReport
    tolerance_signoff_status: ToleranceReviewStatus
    signoff_authority: str
    evaluation_hash: Optional[str] = None
    min_required_sample_count: int = 30
    min_required_tolerance_rate_pct: float = 80.0

    def verify_evidence(self) -> List[str]:
        """
        Executes strict verification of all required evidence components.
        Returns a list of rejection reasons (empty if fully verified).
        """
        rejection_reasons = []

        # 1. Dataset audit checks
        if self.dataset_audit.is_synthetic:
            rejection_reasons.append("REJECTED: DatasetAuditReport confirms dataset contains synthetic data.")
        if self.dataset_audit.gate_status != GateStatus.PASSED:
            rejection_reasons.append(
                f"REJECTED: Dataset audit gate status is '{self.dataset_audit.gate_status.value}', must be PASSED."
            )
        if not self.dataset_audit.has_longitudinal_pairs or self.dataset_audit.sampling_design != SamplingDesign.LONGITUDINAL_PAIRED:
            rejection_reasons.append(
                "REJECTED: Dataset lacks verified longitudinal repeated measurements on identical plots across seasons."
            )
        if self.dataset_audit.row_count < self.min_required_sample_count:
            rejection_reasons.append(
                f"REJECTED: Total dataset rows ({self.dataset_audit.row_count}) below minimum threshold ({self.min_required_sample_count})."
            )

        # 2. Evaluation report checks (leakage safety and holdout design)
        if self.evaluation_report.split_strategy != "GROUPED_PLOT_TIME_SERIES":
            rejection_reasons.append(
                f"REJECTED: Split strategy '{self.evaluation_report.split_strategy}' is not leakage-safe. "
                "Must be 'GROUPED_PLOT_TIME_SERIES'."
            )
        if not self.evaluation_report.data_provenance_verified:
            rejection_reasons.append("REJECTED: Evaluation report does not have verified data provenance.")
        if self.evaluation_report.data_readiness_status != "PASSED":
            rejection_reasons.append(
                f"REJECTED: Evaluation data readiness status is '{self.evaluation_report.data_readiness_status}', must be 'PASSED'."
            )

        # 3. Nutrient-by-nutrient holdout performance checks
        nutrient_summaries = [
            ("Nitrogen", self.evaluation_report.nitrogen_summary),
            ("Phosphorus", self.evaluation_report.phosphorus_summary),
            ("Potassium", self.evaluation_report.potassium_summary),
        ]
        for name, summary in nutrient_summaries:
            if summary.sample_count < self.min_required_sample_count:
                rejection_reasons.append(
                    f"REJECTED: {name} evaluation sample count ({summary.sample_count}) is below required {self.min_required_sample_count} samples."
                )
            if summary.within_tolerance_rate_pct < self.min_required_tolerance_rate_pct:
                rejection_reasons.append(
                    f"REJECTED: {name} within-tolerance rate ({summary.within_tolerance_rate_pct:.1f}%) "
                    f"does not achieve the required {self.min_required_tolerance_rate_pct:.1f}% threshold."
                )
            if summary.target_status != EvaluationTargetStatus.MET:
                rejection_reasons.append(f"REJECTED: {name} target status is '{summary.target_status.value}', must be MET.")

        # 4. Tolerance ratification check
        if self.tolerance_signoff_status != ToleranceReviewStatus.OFFICIALLY_RATIFIED:
            rejection_reasons.append(
                "REJECTED: Nutrient error tolerances are currently PROVISIONAL_PENDING_EXPERT_APPROVAL. "
                "Operational release strictly requires OFFICIALLY_RATIFIED status with documented agronomic sign-off."
            )
        if not self.signoff_authority or not self.signoff_authority.strip():
            rejection_reasons.append("REJECTED: Sign-off authority cannot be empty for official ratification.")

        return rejection_reasons


@dataclass
class ValidationGateDecision:
    task_name: str
    scope: ModelValidationScope
    is_authorized_for_operational_prediction: bool
    rejection_reasons: List[str]
    permitted_uses: List[str]
    actionable_data_requirements: List[str]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "task_name": self.task_name,
            "scope": self.scope.value,
            "is_authorized_for_operational_prediction": self.is_authorized_for_operational_prediction,
            "rejection_reasons": self.rejection_reasons,
            "permitted_uses": self.permitted_uses,
            "actionable_data_requirements": self.actionable_data_requirements,
        }


class ModelValidationGate:
    """
    Guards the prediction engine against executing unauthorized or unvalidated
    empirical inference tasks.
    """

    @classmethod
    def evaluate_task(
        cls,
        task_name: str,
        evidence_bundle: Optional[ValidationEvidenceBundle] = None,
        is_synthetic_data: bool = False,
        cross_sectional_data_available: bool = False,
        # Legacy/test kwargs: strictly rejected if used to assert validation
        longitudinal_data_available: bool = False,
        independent_holdout_evaluated: bool = False,
        tolerance_target_met: bool = False
    ) -> ValidationGateDecision:
        """
        Determines whether a proposed modeling or estimation task is authorized.
        VALIDATED_FOR_SCOPE requires a valid, verified ValidationEvidenceBundle.
        Loose boolean flags cannot grant operational validation.
        """
        rejection_reasons = []
        requirements = []

        # 1. Synthetic data is permanently blocked from operational ground truth
        if is_synthetic_data:
            return ValidationGateDecision(
                task_name=task_name,
                scope=ModelValidationScope.BLOCKED,
                is_authorized_for_operational_prediction=False,
                rejection_reasons=[
                    "REJECTED: Dataset contains synthetic data (e.g., pseudorandom generation artifacts). "
                    "Synthetic labels can never serve as empirical ground truth."
                ],
                permitted_uses=["Synthetic code pipeline sanity checks only."],
                actionable_data_requirements=["Replace synthetic data with certified laboratory test records."]
            )

        # 2. Longitudinal Dynamic Multi-Year Prediction Task
        if task_name.upper() in ["LONGITUDINAL_PREDICTION", "DYNAMIC_NPK_PREDICTION", "OPERATIONAL_ESTIMATE"]:
            # Check if evidence bundle was provided
            if evidence_bundle is None:
                rejection_reasons.append(
                    "REJECTED: No formal ValidationEvidenceBundle provided. Loose boolean flags or manual "
                    "assertions cannot grant VALIDATED_FOR_SCOPE. Operational prediction remains strictly BLOCKED."
                )
                requirements.extend([
                    "Acquire accredited field trial data with at least two genuine laboratory measurements per plot "
                    "separated by at least one complete cropping season with logged management.",
                    "Execute leak-safe GroupKFold / temporal split evaluation on genuine test sets.",
                    "Demonstrate >= 80% tolerance pass rate across N, P, and K with officially ratified agronomic tolerances."
                ])

                return ValidationGateDecision(
                    task_name=task_name,
                    scope=ModelValidationScope.BLOCKED,
                    is_authorized_for_operational_prediction=False,
                    rejection_reasons=rejection_reasons,
                    permitted_uses=[
                        "Agronomic mass-balance bookkeeping ledger tracking only.",
                        "Data sufficiency auditing and missing-data gap detection."
                    ],
                    actionable_data_requirements=requirements
                )

            # If evidence bundle was provided, verify it thoroughly
            bundle_issues = evidence_bundle.verify_evidence()
            if bundle_issues:
                return ValidationGateDecision(
                    task_name=task_name,
                    scope=ModelValidationScope.BLOCKED,
                    is_authorized_for_operational_prediction=False,
                    rejection_reasons=bundle_issues,
                    permitted_uses=[
                        "Agronomic mass-balance bookkeeping ledger tracking only.",
                        "Holdout evaluation gap analysis."
                    ],
                    actionable_data_requirements=[
                        "Remediate all validation evidence deficiencies identified by the gate."
                    ]
                )

            # All evidence verified! Authorize VALIDATED_FOR_SCOPE
            return ValidationGateDecision(
                task_name=task_name,
                scope=ModelValidationScope.VALIDATED_FOR_SCOPE,
                is_authorized_for_operational_prediction=True,
                rejection_reasons=[],
                permitted_uses=[
                    "Operational farm-level NPK estimation within validated crop and soil scope.",
                    "Decision support for seasonal fertilizer scheduling."
                ],
                actionable_data_requirements=[]
            )

        # 3. Cross-Sectional Regional Baseline Exploration Task
        elif task_name.upper() in ["CROSS_SECTIONAL_RESEARCH", "REGIONAL_BASELINE_PRIORS"]:
            if cross_sectional_data_available:
                return ValidationGateDecision(
                    task_name=task_name,
                    scope=ModelValidationScope.RESEARCH_ONLY,
                    is_authorized_for_operational_prediction=False,
                    rejection_reasons=[
                        "Cross-sectional data captures a single point in time and contains no paired re-tests. "
                        "It is scientifically invalid to use cross-sectional data to claim multi-year prediction accuracy."
                    ],
                    permitted_uses=[
                        "Offline statistical analysis of regional baseline NPK distributions (e.g. Latur district SHC).",
                        "Cross-nutrient stoichiometric correlations (e.g. OC vs. Available N).",
                        "OCR certificate format benchmarking."
                    ],
                    actionable_data_requirements=[
                        "To advance beyond RESEARCH_ONLY, longitudinal re-tests on identical plots are mandatory."
                    ]
                )
            else:
                return ValidationGateDecision(
                    task_name=task_name,
                    scope=ModelValidationScope.BLOCKED,
                    is_authorized_for_operational_prediction=False,
                    rejection_reasons=["No verified cross-sectional laboratory dataset available."],
                    permitted_uses=[],
                    actionable_data_requirements=["Load accredited regional Soil Health Card export."]
                )

        # Default fallback for unrecognized tasks
        return ValidationGateDecision(
            task_name=task_name,
            scope=ModelValidationScope.BLOCKED,
            is_authorized_for_operational_prediction=False,
            rejection_reasons=[f"Unrecognized or unauthorized task type: '{task_name}'"],
            permitted_uses=[],
            actionable_data_requirements=["Define a valid research or prediction scope."]
        )

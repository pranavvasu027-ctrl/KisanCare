"""
Safe Abstention Engine & Data Sufficiency Gate
==============================================
Enforces strict scientific criteria for refusing unsupported predictions:
  1. Missing physical baseline laboratory test report.
  2. Unreliable or unverified plot identity.
  3. Excessive time elapsed (> 36 months without management records, or > 60 months absolute).
  4. Unbounded unrecorded cropping gaps (> 240 days between crop seasons).
  5. Insufficient input data coverage score (< 0.40).
  6. Operational prediction validation gate blocked (no longitudinal ground truth).
  7. Invalid units or unverified test methods.

When any of these conditions are met, the engine mandates abstention with
ProvenanceType.INSUFFICIENT_DATA and generates structured, actionable guidance
specifying the missing evidence and certified soil retesting protocol.
"""

from dataclasses import dataclass, field, asdict
from enum import Enum
from typing import Dict, List, Optional, Any
from datetime import datetime

from ml.soil_intelligence.schemas import (
    ProvenanceType,
    MeasuredLaboratoryReport,
    NutrientUnit,
    SoilPredictionRecord
)
from ml.soil_intelligence.model.validation_gate import (
    ModelValidationGate,
    ValidationGateDecision,
    ModelValidationScope
)


class AbstentionReasonCode(str, Enum):
    MISSING_BASELINE_TEST = "MISSING_BASELINE_TEST"
    UNVERIFIED_PLOT_IDENTIFIER = "UNVERIFIED_PLOT_IDENTIFIER"
    EXPIRED_TIME_HORIZON = "EXPIRED_TIME_HORIZON"
    UNRECORDED_CROPPING_GAPS = "UNRECORDED_CROPPING_GAPS"
    INSUFFICIENT_INPUT_COVERAGE = "INSUFFICIENT_INPUT_COVERAGE"
    OPERATIONAL_GATE_BLOCKED = "OPERATIONAL_GATE_BLOCKED"
    UNVERIFIED_LAB_METHOD_OR_UNITS = "UNVERIFIED_LAB_METHOD_OR_UNITS"
    UNSUPPORTED_PREDICTION_SCOPE = "UNSUPPORTED_PREDICTION_SCOPE"


class RetestingUrgency(str, Enum):
    IMMEDIATE_ACTION_REQUIRED = "IMMEDIATE_ACTION_REQUIRED"
    RECOMMENDED_BEFORE_NEXT_SOWING = "RECOMMENDED_BEFORE_NEXT_SOWING"
    ROUTINE_MONITORING = "ROUTINE_MONITORING"


@dataclass
class AbstentionDecision:
    """
    Structured outcome of the data sufficiency and safety evaluation.
    """
    should_abstain: bool
    status: ProvenanceType
    reason_codes: List[AbstentionReasonCode] = field(default_factory=list)
    primary_reason: Optional[str] = None
    detailed_reasons: List[str] = field(default_factory=list)
    missing_evidence: List[str] = field(default_factory=list)
    actionable_recommendations: List[str] = field(default_factory=list)
    retesting_urgency: RetestingUrgency = RetestingUrgency.RECOMMENDED_BEFORE_NEXT_SOWING
    target_sampling_depth_cm: float = 15.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "should_abstain": self.should_abstain,
            "status": self.status.value,
            "reason_codes": [rc.value for rc in self.reason_codes],
            "primary_reason": self.primary_reason,
            "detailed_reasons": self.detailed_reasons,
            "missing_evidence": self.missing_evidence,
            "actionable_recommendations": self.actionable_recommendations,
            "retesting_urgency": self.retesting_urgency.value,
            "target_sampling_depth_cm": self.target_sampling_depth_cm,
        }


class AbstentionEngine:
    """
    Evaluates whether a plot's historical evidence supports an agronomic estimate
    or whether the system must safely abstain.
    """

    MAX_ABSOLUTE_HORIZON_MONTHS: float = 60.0    # 5 years maximum baseline life
    FRESHNESS_WARNING_MONTHS: float = 36.0       # 36 months warning threshold
    MAX_UNRECORDED_GAP_DAYS: int = 240           # >8 months gap between crop seasons
    MIN_COVERAGE_SCORE: float = 0.40             # Minimum coverage threshold

    @classmethod
    def evaluate(
        cls,
        plot_id: str,
        target_date: str,
        baseline_report: Optional[MeasuredLaboratoryReport],
        months_since_baseline: Optional[float],
        coverage_score: float,
        unrecorded_gap_days: int,
        intervening_events_count: int,
        validation_decision: Optional[ValidationGateDecision] = None,
        allow_unvalidated_research: bool = False
    ) -> AbstentionDecision:
        """
        Executes comprehensive safety and sufficiency checks.
        """
        reason_codes: List[AbstentionReasonCode] = []
        detailed_reasons: List[str] = []
        missing_evidence: List[str] = []
        recommendations: List[str] = []
        urgency = RetestingUrgency.ROUTINE_MONITORING

        # 1. Plot Identifier Validation
        if not plot_id or not plot_id.strip() or plot_id.strip().upper() in ["UNKNOWN", "NONE", "NULL"]:
            reason_codes.append(AbstentionReasonCode.UNVERIFIED_PLOT_IDENTIFIER)
            detailed_reasons.append(
                "Plot identifier is missing or unverified. Agronomic soil intelligence requires a "
                "unique, immutable plot or field boundary identifier."
            )
            missing_evidence.append("Valid geo-referenced plot or field survey identifier.")
            recommendations.append("Assign and verify the official plot identifier before querying soil history.")

        # 2. Baseline Laboratory Test Availability
        if baseline_report is None:
            reason_codes.append(AbstentionReasonCode.MISSING_BASELINE_TEST)
            detailed_reasons.append(
                "No physical laboratory soil test report exists in plot history on or before the target date. "
                "Estimating soil nutrients without an empirical physical baseline is scientifically invalid."
            )
            missing_evidence.append(
                "Baseline soil test report from an accredited laboratory with measured N, P, and K values."
            )
            recommendations.append(
                "Collect a representative composite soil sample (0-15 cm plow depth) across the plot "
                "following a zig-zag sampling pattern and submit to a certified laboratory."
            )
            urgency = RetestingUrgency.IMMEDIATE_ACTION_REQUIRED

        else:
            # 3. Laboratory Report Quality & Units
            # Check if baseline requires human review or has invalid units
            if baseline_report.review_required:
                reason_codes.append(AbstentionReasonCode.UNVERIFIED_LAB_METHOD_OR_UNITS)
                detailed_reasons.append(
                    f"Baseline lab report '{baseline_report.report_id}' has unresolved OCR extraction flags "
                    f"or out-of-bounds parameters requiring human agronomic verification."
                )
                missing_evidence.append("Human agronomic review and confirmation of extracted laboratory values.")
                recommendations.append("Complete human verification in the OCR review manager before using this report.")

            # 4. Time Horizon and Freshness
            if months_since_baseline is not None:
                if months_since_baseline > cls.MAX_ABSOLUTE_HORIZON_MONTHS:
                    reason_codes.append(AbstentionReasonCode.EXPIRED_TIME_HORIZON)
                    detailed_reasons.append(
                        f"Baseline soil test is {months_since_baseline:.1f} months old (> {cls.MAX_ABSOLUTE_HORIZON_MONTHS:.0f} month maximum). "
                        "Long-term biological mineralization and environmental leaching exceed validated horizon."
                    )
                    missing_evidence.append(
                        f"Updated laboratory soil test conducted within the last {cls.FRESHNESS_WARNING_MONTHS:.0f} months."
                    )
                    recommendations.append(
                        "Schedule a fresh certified soil test before planning upcoming seasonal fertilizer applications."
                    )
                    urgency = RetestingUrgency.IMMEDIATE_ACTION_REQUIRED

                elif months_since_baseline > cls.FRESHNESS_WARNING_MONTHS and intervening_events_count == 0:
                    reason_codes.append(AbstentionReasonCode.EXPIRED_TIME_HORIZON)
                    detailed_reasons.append(
                        f"Baseline soil test is {months_since_baseline:.1f} months old (> {cls.FRESHNESS_WARNING_MONTHS:.0f} month threshold) "
                        "and zero intervening crop harvests, fertilizer, or manure events were recorded."
                    )
                    missing_evidence.append(
                        "Intervening cropping and fertilization logs, or a fresh laboratory test report."
                    )
                    recommendations.append(
                        "Provide records of historical crops and fertilizer applied since the last soil test, "
                        "or conduct a fresh soil test."
                    )
                    urgency = RetestingUrgency.RECOMMENDED_BEFORE_NEXT_SOWING

            # 5. Cropping Gaps and Input Coverage
            if unrecorded_gap_days > cls.MAX_UNRECORDED_GAP_DAYS:
                reason_codes.append(AbstentionReasonCode.UNRECORDED_CROPPING_GAPS)
                detailed_reasons.append(
                    f"Detected unrecorded cropping gap of {unrecorded_gap_days} days (> {cls.MAX_UNRECORDED_GAP_DAYS} days). "
                    "Unrecorded agricultural seasons produce unbounded nutrient drift."
                )
                missing_evidence.append("Management records for unlogged cropping cycles.")
                recommendations.append("Log harvested crops and fertilizer applications for unrecorded seasons.")

            if coverage_score < cls.MIN_COVERAGE_SCORE:
                reason_codes.append(AbstentionReasonCode.INSUFFICIENT_INPUT_COVERAGE)
                detailed_reasons.append(
                    f"Timeline input coverage score ({coverage_score:.2f}) is below minimum threshold ({cls.MIN_COVERAGE_SCORE:.2f})."
                )
                missing_evidence.append("Comprehensive farm management history.")

        # 6. Operational Validation Gate Authorization Check
        if validation_decision is not None:
            if not validation_decision.is_authorized_for_operational_prediction:
                if not allow_unvalidated_research:
                    reason_codes.append(AbstentionReasonCode.OPERATIONAL_GATE_BLOCKED)
                    detailed_reasons.append(
                        f"Operational prediction is {validation_decision.scope.value}: "
                        + "; ".join(validation_decision.rejection_reasons)
                    )
                    for req in validation_decision.actionable_data_requirements:
                        if req not in missing_evidence:
                            missing_evidence.append(req)

        # Decision synthesis
        should_abstain = len(reason_codes) > 0

        if should_abstain:
            primary = detailed_reasons[0] if detailed_reasons else "Insufficient data to support prediction."
            status = ProvenanceType.INSUFFICIENT_DATA
        else:
            primary = None
            status = ProvenanceType.ESTIMATED

        return AbstentionDecision(
            should_abstain=should_abstain,
            status=status,
            reason_codes=reason_codes,
            primary_reason=primary,
            detailed_reasons=detailed_reasons,
            missing_evidence=missing_evidence,
            actionable_recommendations=recommendations,
            retesting_urgency=urgency,
            target_sampling_depth_cm=15.0
        )

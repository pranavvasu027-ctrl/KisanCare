"""
Data-Readiness Gate & Provenance Verifier
=========================================
Audits soil datasets for physical ground truth integrity.
Enforces the strict rule: NEVER use synthetic data as ground truth.
Blocks unvalidated model training and marks evaluation as NOT_YET_VALIDATED
until genuine, longitudinally paired laboratory data is verified.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Any
import math
import re


class GateStatus(str, Enum):
    PASSED = "PASSED"
    BLOCKED = "BLOCKED"
    NOT_YET_VALIDATED = "NOT_YET_VALIDATED"


class ProvenanceType(str, Enum):
    OFFICIAL_SHC_EXPORT = "OFFICIAL_SHC_EXPORT"      # Official Govt Soil Health Card export
    CERTIFIED_LAB = "CERTIFIED_LAB"                  # Accredited soil testing laboratory report
    RESEARCH_TRIAL = "RESEARCH_TRIAL"                # ICAR / SAU / KVK experimental plot trial
    SYNTHETIC_GENERATED = "SYNTHETIC_GENERATED"      # Algorithmic / pseudorandom generated (REJECTED)
    UNKNOWN = "UNKNOWN"                              # Unverified source (BLOCKED by default)


class SamplingDesign(str, Enum):
    LONGITUDINAL_PAIRED = "LONGITUDINAL_PAIRED"      # Same plot resampled at multiple dates (REQUIRED for time models)
    CROSS_SECTIONAL = "CROSS_SECTIONAL"              # Single point snapshot in time (Useful as regional prior only)
    UNLINKED = "UNLINKED"                            # Isolated samples without plot identifiers


@dataclass
class DatasetAuditReport:
    file_path: str
    row_count: int
    column_count: int
    provenance: ProvenanceType
    sampling_design: SamplingDesign
    is_synthetic: bool
    synthetic_markers: List[str]
    has_nitrogen: bool
    has_phosphorus: bool
    has_potassium: bool
    has_ph: bool
    has_sample_dates: bool
    has_plot_identifiers: bool
    has_longitudinal_pairs: bool
    gate_status: GateStatus
    rejection_reasons: List[str]
    actionable_recommendations: List[str]
    summary_metrics: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "file_path": self.file_path,
            "row_count": self.row_count,
            "column_count": self.column_count,
            "provenance": self.provenance.value,
            "sampling_design": self.sampling_design.value,
            "is_synthetic": self.is_synthetic,
            "synthetic_markers": self.synthetic_markers,
            "has_nitrogen": self.has_nitrogen,
            "has_phosphorus": self.has_phosphorus,
            "has_potassium": self.has_potassium,
            "has_ph": self.has_ph,
            "has_sample_dates": self.has_sample_dates,
            "has_plot_identifiers": self.has_plot_identifiers,
            "has_longitudinal_pairs": self.has_longitudinal_pairs,
            "gate_status": self.gate_status.value,
            "rejection_reasons": self.rejection_reasons,
            "actionable_recommendations": self.actionable_recommendations,
            "summary_metrics": self.summary_metrics,
        }


class DataReadinessGate:
    """
    Enforces quality, provenance, and non-synthetic standards on candidate
    datasets before any training or accuracy evaluation is allowed.
    """

    @staticmethod
    def detect_synthetic_markers(rows: List[Dict[str, Any]], generator_code: Optional[str] = None) -> List[str]:
        """
        Inspects raw data rows and optional source code for signatures of synthetic data generation.
        """
        markers = []

        if generator_code:
            code_lower = generator_code.lower()
            suspicious_patterns = [
                ("np.random.gamma", "Uses NumPy gamma distribution generator"),
                ("np.random.normal", "Uses NumPy normal distribution generator"),
                ("random.choice", "Uses pseudorandom categorical selection"),
                ("np.clip", "Uses artificial range clipping"),
                ("fake", "Source code explicitly references fake data"),
                ("synthetic", "Source code explicitly references synthetic generation"),
            ]
            for pattern, desc in suspicious_patterns:
                if pattern in code_lower:
                    markers.append(desc)

        if not rows:
            return markers

        # Statistical artifact detection
        for target in ['nitrogen', 'phosphorus', 'potassium', 'pH']:
            vals = []
            for r in rows:
                v = r.get(target)
                if v is not None and v != "":
                    try:
                        vals.append(float(v))
                    except (ValueError, TypeError):
                        pass

            if len(vals) >= 30:
                # 1. Perfectly rounded decimal artifacts
                fractional_parts = [v - math.floor(v) for v in vals]
                all_exact_decimals = all(round(f, 2) == f for f in fractional_parts)
                if all_exact_decimals and len(set(fractional_parts)) > 10:
                    # Often produced by round(val, 2) in synthetic code
                    pass

                # 2. Check for unrealistic physical boundaries
                if target == 'pH' and (min(vals) < 2.0 or max(vals) > 12.0):
                    markers.append(f"Unrealistic pH values detected (range: {min(vals)} - {max(vals)})")
                if target in ['nitrogen', 'phosphorus', 'potassium'] and min(vals) < 0:
                    markers.append(f"Negative {target} concentration detected")

        return markers

    @classmethod
    def audit_tabular_records(
        cls,
        file_path: str,
        rows: List[Dict[str, Any]],
        columns: List[str],
        declared_provenance: ProvenanceType = ProvenanceType.UNKNOWN,
        generator_code: Optional[str] = None
    ) -> DatasetAuditReport:
        """
        Audits a tabular dataset against all KISANcare ground-truth requirements.
        """
        cols_lower = [c.lower().strip() for c in columns]
        row_count = len(rows)
        rejection_reasons = []
        recommendations = []

        # 1. Check required nutrient and soil attributes
        has_n = any(c in cols_lower for c in ['nitrogen', 'n', 'available_n', 'soil_n'])
        has_p = any(c in cols_lower for c in ['phosphorus', 'p', 'available_p', 'soil_p', 'p2o5'])
        has_k = any(c in cols_lower for c in ['potassium', 'k', 'available_k', 'soil_k', 'k2o'])
        has_ph = any(c in cols_lower for c in ['ph', 'soil_ph', 'reaction'])
        has_dates = any(c in cols_lower for c in ['date', 'sample_date', 'test_date', 'timestamp', 'cycle', 'year'])
        has_plots = any(c in cols_lower for c in ['plot_id', 'field_id', 'survey_no', 'sample_no', 'farmer_id'])

        if not has_n: rejection_reasons.append("Missing Nitrogen (N) measurements")
        if not has_p: rejection_reasons.append("Missing Phosphorus (P) measurements")
        if not has_k: rejection_reasons.append("Missing Potassium (K) measurements")
        if not has_ph: rejection_reasons.append("Missing pH measurements")

        # 2. Synthetic data check
        synthetic_markers = cls.detect_synthetic_markers(rows, generator_code)
        is_synthetic = (
            declared_provenance == ProvenanceType.SYNTHETIC_GENERATED or
            len(synthetic_markers) > 0
        )

        if is_synthetic:
            rejection_reasons.append(
                f"REJECTED: Dataset contains synthetic data ({'; '.join(synthetic_markers) if synthetic_markers else 'Declared synthetic'})"
            )
            recommendations.append(
                "Never use synthetic data for ground-truth validation. Ingest genuine laboratory records."
            )

        # 3. Longitudinal pairing check
        has_longitudinal_pairs = False
        sampling_design = SamplingDesign.UNLINKED

        if has_plots and has_dates:
            plot_col = next(c for c in columns if c.lower().strip() in ['plot_id', 'field_id', 'survey_no', 'sample_no', 'farmer_id'])
            date_col = next(c for c in columns if c.lower().strip() in ['date', 'sample_date', 'test_date', 'timestamp', 'cycle', 'year'])

            plot_samples: Dict[str, set] = {}
            for r in rows:
                p_val = str(r.get(plot_col, "")).strip()
                d_val = str(r.get(date_col, "")).strip()
                if p_val and d_val:
                    if p_val not in plot_samples:
                        plot_samples[p_val] = set()
                    plot_samples[p_val].add(d_val)

            paired_plots = [p for p, dates in plot_samples.items() if len(dates) >= 2]
            if len(paired_plots) >= 10:
                has_longitudinal_pairs = True
                sampling_design = SamplingDesign.LONGITUDINAL_PAIRED
            elif len(rows) > 0:
                sampling_design = SamplingDesign.CROSS_SECTIONAL
        elif has_plots:
            sampling_design = SamplingDesign.CROSS_SECTIONAL

        if not has_longitudinal_pairs and not is_synthetic:
            rejection_reasons.append(
                "Lacks longitudinal pairing: No repeat measurements of the same plot across multiple dates were identified."
            )
            recommendations.append(
                "Cross-sectional snapshots can establish baseline regional priors, but multi-year progression models require paired re-tests on the same plot."
            )

        # Determine Gate Status
        if is_synthetic or not (has_n and has_p and has_k):
            gate_status = GateStatus.BLOCKED
        elif not has_longitudinal_pairs:
            # Clean genuine data, but insufficient for multi-year dynamic validation
            gate_status = GateStatus.NOT_YET_VALIDATED
        else:
            gate_status = GateStatus.PASSED

        return DatasetAuditReport(
            file_path=file_path,
            row_count=row_count,
            column_count=len(columns),
            provenance=declared_provenance,
            sampling_design=sampling_design,
            is_synthetic=is_synthetic,
            synthetic_markers=synthetic_markers,
            has_nitrogen=has_n,
            has_phosphorus=has_p,
            has_potassium=has_k,
            has_ph=has_ph,
            has_sample_dates=has_dates,
            has_plot_identifiers=has_plots,
            has_longitudinal_pairs=has_longitudinal_pairs,
            gate_status=gate_status,
            rejection_reasons=rejection_reasons,
            actionable_recommendations=recommendations,
            summary_metrics={"total_rows": row_count, "unique_columns": len(columns)}
        )

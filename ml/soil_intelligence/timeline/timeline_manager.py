"""
Dynamic Multi-Year Timeline Manager
===================================
Maintains chronological farm plot histories across 2023, 2024, 2025, 2026,
and any other available years without requiring rigid annual cadences.
Coordinates laboratory baselines, crop harvests, fertilizer events,
identifies unrecorded gaps, and generates mass-balance ledgers.
"""

from dataclasses import dataclass, field, asdict
from enum import Enum
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime, date

from ml.soil_intelligence.schemas import (
    MeasuredLaboratoryReport,
    AgronomicEvent,
    ModelledEnvironmentalContext,
    ProvenanceType
)
from ml.soil_intelligence.timeline.agronomic_depletion import (
    AgronomicDepletionEngine,
    NutrientFluxEvent,
    CumulativeMassBalanceLedger
)


@dataclass
class TimelineSufficiencyAssessment:
    """
    Evaluates whether historical records for a plot are sufficient to generate
    an estimate, or whether the system must abstain with INSUFFICIENT_DATA.
    """
    plot_id: str
    target_date: str
    has_baseline_test: bool
    baseline_report_id: Optional[str]
    baseline_date: Optional[str]
    months_since_baseline: Optional[float]
    freshness_warning: bool                  # True if > 36 months
    is_sufficient: bool
    coverage_score: float                    # [0.0, 1.0]
    unrecorded_gap_days: int
    abstain_reason: Optional[str] = None
    agronomic_advice: Optional[str] = None


class PlotTimelineManager:
    """
    Maintains and audits the multi-year chronological event history for a farm plot.
    """

    def __init__(self, plot_id: str, farm_id: Optional[str] = None):
        self.plot_id = plot_id
        self.farm_id = farm_id
        self.lab_reports: List[MeasuredLaboratoryReport] = []
        self.flux_events: List[NutrientFluxEvent] = []
        self.raw_agronomic_events: List[AgronomicEvent] = []
        self.environmental_context: Optional[ModelledEnvironmentalContext] = None

    def add_lab_report(self, report: MeasuredLaboratoryReport) -> None:
        """Adds a verified laboratory soil test report (MEASURED provenance)."""
        if report.plot_id != self.plot_id:
            raise ValueError(f"Report plot_id '{report.plot_id}' does not match timeline plot_id '{self.plot_id}'")
        if report.provenance != ProvenanceType.MEASURED:
            raise ValueError(
                f"Only reports with ProvenanceType.MEASURED can be added as baseline laboratory tests. "
                f"Received provenance: '{report.provenance}'"
            )
        if report.notes and any(marker in report.notes.lower() for marker in ["synthetic", "fake", "random.gamma"]):
            raise ValueError("Rejected synthetic laboratory report from physical farm timeline.")
        if report.lab_name and any(marker in report.lab_name.lower() for marker in ["synthetic", "fake", "random.gamma"]):
            raise ValueError("Rejected synthetic laboratory report from physical farm timeline.")

        self.lab_reports.append(report)
        # Keep sorted chronologically
        self.lab_reports.sort(key=lambda r: r.sample_date)

    def record_crop_harvest(
        self,
        crop_name: str,
        yield_tons_ha: float,
        harvest_date: str,
        event_id: Optional[str] = None,
        residue_retained: bool = False
    ) -> NutrientFluxEvent:
        """Records a crop harvest depletion event."""
        eid = event_id or f"HARVEST_{self.plot_id}_{harvest_date}"
        flux = AgronomicDepletionEngine.calculate_crop_removal(
            crop_name=crop_name,
            yield_tons_ha=yield_tons_ha,
            event_date=harvest_date,
            event_id=eid,
            residue_retained=residue_retained
        )
        self.flux_events.append(flux)
        self.flux_events.sort(key=lambda e: e.event_date)
        return flux

    def record_fertilizer_application(
        self,
        fertilizer_name: str,
        application_rate_kg_ha: float,
        application_date: str,
        event_id: Optional[str] = None
    ) -> NutrientFluxEvent:
        """Records a mineral fertilizer or organic manure application event."""
        eid = event_id or f"FERT_{self.plot_id}_{application_date}"
        flux = AgronomicDepletionEngine.calculate_fertilizer_input(
            fertilizer_name=fertilizer_name,
            application_rate_kg_ha=application_rate_kg_ha,
            event_date=application_date,
            event_id=eid
        )
        self.flux_events.append(flux)
        self.flux_events.sort(key=lambda e: e.event_date)
        return flux

    def set_environmental_context(self, context: ModelledEnvironmentalContext) -> None:
        """Attaches auxiliary regional raster context (SoilGrids texture)."""
        self.environmental_context = context

    def get_latest_baseline_report(self, target_date: str) -> Optional[MeasuredLaboratoryReport]:
        """Finds the most recent laboratory test performed on or before target_date."""
        eligible = [r for r in self.lab_reports if r.sample_date <= target_date]
        if not eligible:
            return None
        return eligible[-1]

    def assess_data_sufficiency(
        self,
        target_date: str,
        freshness_threshold_months: float = 36.0
    ) -> TimelineSufficiencyAssessment:
        """
        Evaluates whether historical records are adequate to generate a defensible estimate.
        Adheres to Condition 3: 36 months is a provisional warning threshold, not an automatic
        disqualification if intervening records, coverage, and uncertainty are acceptable.
        """
        baseline = self.get_latest_baseline_report(target_date)

        if not baseline:
            return TimelineSufficiencyAssessment(
                plot_id=self.plot_id,
                target_date=target_date,
                has_baseline_test=False,
                baseline_report_id=None,
                baseline_date=None,
                months_since_baseline=None,
                freshness_warning=True,
                is_sufficient=False,
                coverage_score=0.0,
                unrecorded_gap_days=0,
                abstain_reason="No physical laboratory soil test report exists in plot history.",
                agronomic_advice="A baseline laboratory soil test is required before soil nutrient estimation can begin."
            )

        # Calculate time elapsed
        try:
            d_base = datetime.strptime(baseline.sample_date[:10], "%Y-%m-%d")
            d_target = datetime.strptime(target_date[:10], "%Y-%m-%d")
            days_elapsed = (d_target - d_base).days
            months_elapsed = round(days_elapsed / 30.4375, 1)
        except Exception:
            days_elapsed = 0
            months_elapsed = 0.0

        freshness_warning = months_elapsed > freshness_threshold_months

        # Find intervening events between baseline and target date
        intervening_flux = [
            e for e in self.flux_events
            if baseline.sample_date < e.event_date <= target_date
        ]

        # Check for unrecorded gaps (>240 days without any logged activity)
        all_dates = sorted([baseline.sample_date] + [e.event_date for e in intervening_flux] + [target_date])
        max_gap_days = 0
        total_gap_days = 0
        for i in range(len(all_dates) - 1):
            try:
                d1 = datetime.strptime(all_dates[i][:10], "%Y-%m-%d")
                d2 = datetime.strptime(all_dates[i+1][:10], "%Y-%m-%d")
                gap = (d2 - d1).days
                if gap > 240:
                    total_gap_days += (gap - 240)
                    if gap > max_gap_days:
                        max_gap_days = gap
            except Exception:
                pass

        # Compute coverage score
        if days_elapsed <= 0:
            coverage = 1.0
        else:
            unrecorded_ratio = min(1.0, total_gap_days / max(1, days_elapsed))
            coverage = round(max(0.10, 1.0 - (0.5 * unrecorded_ratio) - (0.2 * (months_elapsed / 60.0))), 2)

        # Abstention decision:
        # If > 36 months elapsed AND zero intervening records were logged, the evidence is insufficient.
        if freshness_warning and len(intervening_flux) == 0:
            is_sufficient = False
            abstain_reason = (
                f"Baseline soil test is {months_elapsed:.0f} months old (> {freshness_threshold_months:.0f} month threshold) "
                f"and zero intervening crop harvests or fertilizer applications were recorded."
            )
            advice = "Field nutrient status has drifted beyond defensible bounds. A fresh laboratory soil test is strongly recommended."
        # If > 60 months (5 years) elapsed regardless of records, model applicability expires
        elif months_elapsed > 60.0:
            is_sufficient = False
            abstain_reason = (
                f"Baseline soil test is {months_elapsed:.0f} months old (> 5 years). "
                f"Soil biological and chemical drift exceeds validated estimation horizons."
            )
            advice = "Long-term soil baseline expired. Schedule a fresh certified soil test before planning seasonal fertilization."
        else:
            is_sufficient = True
            abstain_reason = None
            advice = None

        return TimelineSufficiencyAssessment(
            plot_id=self.plot_id,
            target_date=target_date,
            has_baseline_test=True,
            baseline_report_id=baseline.report_id,
            baseline_date=baseline.sample_date,
            months_since_baseline=months_elapsed,
            freshness_warning=freshness_warning,
            is_sufficient=is_sufficient,
            coverage_score=coverage,
            unrecorded_gap_days=total_gap_days,
            abstain_reason=abstain_reason,
            agronomic_advice=advice
        )

    def get_mass_balance_ledger(
        self,
        target_date: str,
        start_date: Optional[str] = None
    ) -> CumulativeMassBalanceLedger:
        """
        Compiles the nutrient mass-balance ledger from the baseline test date
        (or explicit start_date) up to the target date.
        """
        if not start_date:
            baseline = self.get_latest_baseline_report(target_date)
            start_date = baseline.sample_date if baseline else target_date

        sufficiency = self.assess_data_sufficiency(target_date)

        return AgronomicDepletionEngine.compile_cumulative_ledger(
            plot_id=self.plot_id,
            start_date=start_date,
            end_date=target_date,
            flux_events=self.flux_events,
            known_unrecorded_days=sufficiency.unrecorded_gap_days,
            unrecorded_crop_cycles=(sufficiency.coverage_score < 0.50 and len(self.flux_events) == 0)
        )

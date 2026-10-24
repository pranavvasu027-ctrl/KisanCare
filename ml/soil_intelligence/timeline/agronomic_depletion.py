"""
Agronomic Depletion, Replenishment & Nutrient Mass-Balance Engine
=================================================================
Calculates nutrient additions from mineral fertilizers and organic manures,
and nutrient removals from crop harvest biomass, using documented, defensible
agronomic coefficients (ICAR / Tandon 2004 / IPNI standards).

CRITICAL SCIENTIFIC PRINCIPLE:
Nutrient mass balance (Gross Additions - Gross Removals) represents the
agronomic ledger of the plot. It is NOT a direct chemical soil extractable
NPK concentration (which is governed by mineral adsorption, fixation kinetics,
cation exchange capacity, and microbial immobilization).
"""

from dataclasses import dataclass, field, asdict
from enum import Enum
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime
import math

from ml.soil_intelligence.schemas import (
    NutrientUnit,
    ChemicalForm,
    ProvenanceType,
    FACTOR_P2O5_TO_P,
    FACTOR_K2O_TO_K
)


# =====================================================================
# 1. AGRONOMIC COEFFICIENTS (DEFENSIBLE BENCHMARKS)
# =====================================================================

@dataclass(frozen=True)
class CropRemovalBenchmark:
    """
    Standard nutrient removal per metric ton (1000 kg) of economic yield.
    Source: ICAR Handbook of Agriculture / Tandon (2004) / IPNI Agronomy Factsheets.
    """
    crop_name: str
    n_kg_per_ton: float                      # Total plant uptake per ton grain/product
    p_elemental_kg_per_ton: float            # Elemental P removed per ton economic yield
    k_elemental_kg_per_ton: float            # Elemental K removed per ton economic yield
    bnf_nitrogen_fraction: float             # Biological Nitrogen Fixation fraction (0.0 for non-legumes)
    straw_stover_ratio: float                # Weight of stover/straw relative to economic yield
    straw_k_retention_fraction: float        # Fraction of total plant K residing in straw/stover
    source_citation: str
    max_plausible_yield_tons_ha: Optional[float] = None  # Traceable maximum plausible economic yield
    yield_basis: str = "ECONOMIC_HARVEST_PRODUCT"        # Crop-specific harvest product basis
    yield_source_citation: Optional[str] = None          # Traceable reference for yield bound

    @property
    def net_soil_n_kg_per_ton(self) -> float:
        """Net soil N removal after subtracting biologically fixed atmospheric N."""
        return self.n_kg_per_ton * (1.0 - self.bnf_nitrogen_fraction)

    @property
    def p2o5_equivalent_kg_per_ton(self) -> float:
        return self.p_elemental_kg_per_ton / FACTOR_P2O5_TO_P

    @property
    def k2o_equivalent_kg_per_ton(self) -> float:
        return self.k_elemental_kg_per_ton / FACTOR_K2O_TO_K


# Verified agronomic crop removal database with crop-specific plausibility bounds
CROP_REMOVAL_BENCHMARKS: Dict[str, CropRemovalBenchmark] = {
    "wheat": CropRemovalBenchmark(
        crop_name="Wheat",
        n_kg_per_ton=24.5,
        p_elemental_kg_per_ton=3.8,          # ~8.7 kg P2O5/ton
        k_elemental_kg_per_ton=20.0,         # ~24.1 kg K2O/ton
        bnf_nitrogen_fraction=0.0,
        straw_stover_ratio=1.2,
        straw_k_retention_fraction=0.75,
        source_citation="ICAR Handbook of Agriculture (6th Ed.); Tandon H.L.S. (2004)",
        max_plausible_yield_tons_ha=8.5,
        yield_basis="Clean Dry Grain (~12% moisture)",
        yield_source_citation="ICAR-IIWBR Karnal / Directorate of Economics and Statistics (DES); irrigated maximum trial yields"
    ),
    "rice": CropRemovalBenchmark(
        crop_name="Rice",
        n_kg_per_ton=20.0,
        p_elemental_kg_per_ton=3.5,          # ~8.0 kg P2O5/ton
        k_elemental_kg_per_ton=25.0,         # ~30.1 kg K2O/ton
        bnf_nitrogen_fraction=0.0,
        straw_stover_ratio=1.3,
        straw_k_retention_fraction=0.80,
        source_citation="ICAR Directorate of Rice Research / Tandon (2004)",
        max_plausible_yield_tons_ha=9.0,
        yield_basis="Rough Paddy Grain (~14% moisture)",
        yield_source_citation="ICAR-NRRI Cuttack / ICAR-IIRR Hyderabad; all-India high-yield irrigated records"
    ),
    "maize": CropRemovalBenchmark(
        crop_name="Maize",
        n_kg_per_ton=22.0,
        p_elemental_kg_per_ton=4.0,          # ~9.2 kg P2O5/ton
        k_elemental_kg_per_ton=18.0,         # ~21.7 kg K2O/ton
        bnf_nitrogen_fraction=0.0,
        straw_stover_ratio=1.1,
        straw_k_retention_fraction=0.70,
        source_citation="ICAR Indian Institute of Maize Research",
        max_plausible_yield_tons_ha=12.0,
        yield_basis="Shelled Grain",
        yield_source_citation="ICAR-IIMR Ludhiana / PAU; single-cross hybrid maximum yield bounds"
    ),
    "soybean": CropRemovalBenchmark(
        crop_name="Soybean",
        n_kg_per_ton=65.0,                   # Total uptake high, but 55% from biological N2 fixation
        p_elemental_kg_per_ton=6.0,          # ~13.7 kg P2O5/ton
        k_elemental_kg_per_ton=22.0,         # ~26.5 kg K2O/ton
        bnf_nitrogen_fraction=0.55,          # Net soil N removal is 65 * 0.45 = 29.25 kg/ton
        straw_stover_ratio=1.0,
        straw_k_retention_fraction=0.50,
        source_citation="ICAR-IISR Indore; Salvagiotti et al. (2008) BNF synthesis",
        max_plausible_yield_tons_ha=4.5,
        yield_basis="Clean Seed",
        yield_source_citation="ICAR-IISR Indore (Directorate of Soybean Research); Vertisol trial maximums"
    ),
    "cotton": CropRemovalBenchmark(
        crop_name="Cotton",
        n_kg_per_ton=42.0,                   # Per ton of seed-cotton
        p_elemental_kg_per_ton=6.5,          # ~14.9 kg P2O5/ton
        k_elemental_kg_per_ton=38.0,         # ~45.8 kg K2O/ton
        bnf_nitrogen_fraction=0.0,
        straw_stover_ratio=2.5,              # Stalks/biomass
        straw_k_retention_fraction=0.65,
        source_citation="Central Institute for Cotton Research (CICR Nagpur)",
        max_plausible_yield_tons_ha=4.5,
        yield_basis="Seed-Cotton (kapas)",
        yield_source_citation="ICAR-CICR Nagpur; Central Zone irrigated Bt-cotton maximum productivity"
    ),
    "sugarcane": CropRemovalBenchmark(
        crop_name="Sugarcane",
        n_kg_per_ton=1.4,                    # Per ton of fresh millable cane
        p_elemental_kg_per_ton=0.35,         # ~0.8 kg P2O5/ton
        k_elemental_kg_per_ton=2.2,          # ~2.65 kg K2O/ton
        bnf_nitrogen_fraction=0.0,
        straw_stover_ratio=0.25,             # Trash/tops
        straw_k_retention_fraction=0.60,
        source_citation="ICAR-Sugarcane Breeding Institute (SBI Coimbatore)",
        max_plausible_yield_tons_ha=180.0,
        yield_basis="Fresh Millable Stalks",
        yield_source_citation="ICAR-SBI Coimbatore / VSI Pune; tropical Maharashtra Adsali cane records"
    ),
    "pigeon pea": CropRemovalBenchmark(
        crop_name="Pigeon Pea",
        n_kg_per_ton=40.0,
        p_elemental_kg_per_ton=4.2,          # ~9.6 kg P2O5/ton
        k_elemental_kg_per_ton=16.0,         # ~19.3 kg K2O/ton
        bnf_nitrogen_fraction=0.65,          # High BNF pulse; net soil N removal = 14.0 kg/ton
        straw_stover_ratio=2.0,
        straw_k_retention_fraction=0.70,
        source_citation="ICRISAT / ICAR-IIPR Kanpur",
        max_plausible_yield_tons_ha=3.0,
        yield_basis="Clean Seed / Grain",
        yield_source_citation="ICAR-IIPR Kanpur / ICRISAT; long-duration irrigated trial bounds"
    ),
    "gram": CropRemovalBenchmark(
        crop_name="Gram",
        n_kg_per_ton=38.0,
        p_elemental_kg_per_ton=3.6,          # ~8.2 kg P2O5/ton
        k_elemental_kg_per_ton=15.0,         # ~18.1 kg K2O/ton
        bnf_nitrogen_fraction=0.65,
        straw_stover_ratio=1.0,
        straw_k_retention_fraction=0.60,
        source_citation="ICAR Indian Institute of Pulses Research (IIPR Kanpur)",
        max_plausible_yield_tons_ha=3.5,
        yield_basis="Clean Seed / Grain",
        yield_source_citation="ICAR-IIPR Kanpur / MPKV Rahuri; irrigated chickpea trial bounds"
    ),
    "sorghum": CropRemovalBenchmark(
        crop_name="Sorghum",
        n_kg_per_ton=22.5,
        p_elemental_kg_per_ton=3.5,
        k_elemental_kg_per_ton=21.0,
        bnf_nitrogen_fraction=0.0,
        straw_stover_ratio=1.5,
        straw_k_retention_fraction=0.75,
        source_citation="ICAR Indian Institute of Millets Research (IIMR Hyderabad)",
        max_plausible_yield_tons_ha=6.0,
        yield_basis="Grain",
        yield_source_citation="ICAR-IIMR Hyderabad; kharif hybrid high-yield benchmark"
    )
}


@dataclass(frozen=True)
class FertilizerGradeBenchmark:
    """
    Standard nutrient content fractions for mineral and organic fertilizers.
    Source: Fertilizer (Control) Order (FCO) 1985 / ICAR Standards.
    """
    fertilizer_name: str
    n_fraction: float                        # Elemental N (e.g., 0.46 for urea)
    p2o5_fraction: float                     # Guaranteed Phosphate (P2O5)
    k2o_fraction: float                      # Guaranteed Potash (K2O)
    is_organic: bool
    first_year_n_availability: float         # 1.0 for mineral; ~0.30 for FYM due to mineralization kinetics
    source_citation: str

    @property
    def p_elemental_fraction(self) -> float:
        return self.p2o5_fraction * FACTOR_P2O5_TO_P

    @property
    def k_elemental_fraction(self) -> float:
        return self.k2o_fraction * FACTOR_K2O_TO_K


FERTILIZER_GRADE_BENCHMARKS: Dict[str, FertilizerGradeBenchmark] = {
    "urea": FertilizerGradeBenchmark(
        fertilizer_name="Urea",
        n_fraction=0.46,
        p2o5_fraction=0.0,
        k2o_fraction=0.0,
        is_organic=False,
        first_year_n_availability=1.0,
        source_citation="Fertiliser (Control) Order (FCO) 1985 Schedule 1"
    ),
    "dap": FertilizerGradeBenchmark(
        fertilizer_name="Di-Ammonium Phosphate (DAP)",
        n_fraction=0.18,
        p2o5_fraction=0.46,                  # ~20.08% elemental P
        k2o_fraction=0.0,
        is_organic=False,
        first_year_n_availability=1.0,
        source_citation="FCO 1985 18-46-0 specification"
    ),
    "mop": FertilizerGradeBenchmark(
        fertilizer_name="Muriate of Potash (MOP)",
        n_fraction=0.0,
        p2o5_fraction=0.0,
        k2o_fraction=0.60,                  # ~49.81% elemental K
        is_organic=False,
        first_year_n_availability=1.0,
        source_citation="FCO 1985 Potassium Chloride (60% K2O)"
    ),
    "ssp": FertilizerGradeBenchmark(
        fertilizer_name="Single Super Phosphate (SSP)",
        n_fraction=0.0,
        p2o5_fraction=0.16,                  # ~6.98% elemental P (plus 11-12% S)
        k2o_fraction=0.0,
        is_organic=False,
        first_year_n_availability=1.0,
        source_citation="FCO 1985 Single Super Phosphate (16% P2O5)"
    ),
    "10:26:26": FertilizerGradeBenchmark(
        fertilizer_name="NPK Complex 10:26:26",
        n_fraction=0.10,
        p2o5_fraction=0.26,
        k2o_fraction=0.26,
        is_organic=False,
        first_year_n_availability=1.0,
        source_citation="FCO 1985 Complex Fertilizer 10-26-26"
    ),
    "12:32:16": FertilizerGradeBenchmark(
        fertilizer_name="NPK Complex 12:32:16",
        n_fraction=0.12,
        p2o5_fraction=0.32,
        k2o_fraction=0.16,
        is_organic=False,
        first_year_n_availability=1.0,
        source_citation="FCO 1985 Complex Fertilizer 12-32-16"
    ),
    "20:20:0:13": FertilizerGradeBenchmark(
        fertilizer_name="Ammonium Phosphate Sulphate 20:20:0:13",
        n_fraction=0.20,
        p2o5_fraction=0.20,
        k2o_fraction=0.0,
        is_organic=False,
        first_year_n_availability=1.0,
        source_citation="FCO 1985 20-20-0-13 grade"
    ),
    "fym": FertilizerGradeBenchmark(
        fertilizer_name="Farmyard Manure (FYM)",
        n_fraction=0.005,                    # 0.5% N
        p2o5_fraction=0.002,                 # 0.2% P2O5 (~0.087% elemental P)
        k2o_fraction=0.005,                  # 0.5% K2O (~0.415% elemental K)
        is_organic=True,
        first_year_n_availability=0.30,      # Only ~30% mineralizes in Year 1
        source_citation="ICAR Handbook of Agriculture; Tandon (2004)"
    ),
    "vermicompost": FertilizerGradeBenchmark(
        fertilizer_name="Vermicompost",
        n_fraction=0.015,                    # 1.5% N
        p2o5_fraction=0.010,                 # 1.0% P2O5 (~0.436% elemental P)
        k2o_fraction=0.012,                  # 1.2% K2O (~0.996% elemental K)
        is_organic=True,
        first_year_n_availability=0.45,
        source_citation="ICAR-CRIDA Hyderabad / FCO 2006 Organic Standards"
    )
}


# =====================================================================
# 2. NUTRIENT FLUX EVENT & MASS-BALANCE DATA MODELS
# =====================================================================

@dataclass
class NutrientFluxEvent:
    """
    Individual nutrient flux event (addition or depletion) calculated for a plot.
    """
    event_id: str
    event_date: str                          # ISO-8601 (YYYY-MM-DD)
    event_type: str                          # 'FERTILIZER_ADDITION', 'CROP_DEPLETION', 'MANURE_ADDITION'
    description: str
    delta_n_kg_ha: float                     # Positive for addition, negative for crop removal
    delta_p_elemental_kg_ha: float           # Elemental P (kg/ha)
    delta_k_elemental_kg_ha: float           # Elemental K (kg/ha)
    uncertainty_n_kg_ha: float               # ± std / bound
    uncertainty_p_kg_ha: float
    uncertainty_k_kg_ha: float
    calculation_method: str
    assumptions: List[str]
    source_citation: str
    provenance: ProvenanceType = ProvenanceType.FARMER_RECORDED
    raw_reported_yield_tons_ha: Optional[float] = None  # Verbatim reported yield without clamping
    review_required: bool = False
    review_flags: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d['provenance'] = self.provenance.value
        return d


@dataclass
class CumulativeMassBalanceLedger:
    """
    Cumulative accounting ledger of additions and removals between two dates.
    EXPLICITLY DISTINGUISHED from chemical extractable soil NPK concentration.
    """
    plot_id: str
    start_date: str
    end_date: str
    days_elapsed: int

    # Gross additions
    gross_n_added_kg_ha: float = 0.0
    gross_p_added_kg_ha: float = 0.0         # Elemental P
    gross_k_added_kg_ha: float = 0.0         # Elemental K

    # Gross removals
    gross_n_removed_kg_ha: float = 0.0
    gross_p_removed_kg_ha: float = 0.0       # Elemental P
    gross_k_removed_kg_ha: float = 0.0       # Elemental K

    # Net ledger balance (Additions - Removals)
    net_balance_n_kg_ha: float = 0.0
    net_balance_p_kg_ha: float = 0.0
    net_balance_k_kg_ha: float = 0.0

    # Propagated uncertainty bounds (95% confidence bounds on balance)
    balance_uncertainty_n_kg_ha: float = 0.0
    balance_uncertainty_p_kg_ha: float = 0.0
    balance_uncertainty_k_kg_ha: float = 0.0

    # Quality & missing event indicators
    has_unrecorded_crop_cycles: bool = False
    has_unrecorded_fertilizer_periods: bool = False
    unrecorded_days_estimate: int = 0
    input_coverage_score: float = 1.0        # [0.0, 1.0]
    data_quality_flags: List[str] = field(default_factory=list)
    has_unreviewed_suspicious_events: bool = False

    disclaimer: str = (
        "CRITICAL SCIENTIFIC DISTINCTION: This cumulative nutrient mass-balance reflects "
        "the physical additions minus crop removals on the field. It is NOT a direct measure "
        "of current extractable soil test available NPK. Soil test values depend on soil buffering, "
        "mineral fixation, microbial cycling, and leaching losses."
    )

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


# =====================================================================
# 3. AGRONOMIC DEPLETION & REPLENISHMENT ENGINE
# =====================================================================

class AgronomicDepletionEngine:
    """
    Computes nutrient flux for individual agronomic management events
    and compiles the cumulative multi-year mass-balance ledger.
    """

    @classmethod
    def calculate_crop_removal(
        cls,
        crop_name: str,
        yield_tons_ha: float,
        event_date: str,
        event_id: str = "CROP_HARVEST",
        residue_retained: bool = False
    ) -> NutrientFluxEvent:
        """
        Calculates N, P, K removal for a harvested crop using ICAR benchmarks.
        Applies crop-specific upper plausibility boundaries; flags suspicious high yields
        for human agronomic review while strictly preserving raw reported values without clamping.
        """
        if yield_tons_ha <= 0:
            raise ValueError(f"Harvest yield must be strictly positive: {yield_tons_ha}")

        key = crop_name.strip().lower()
        review_required = False
        review_flags: List[str] = []

        if key not in CROP_REMOVAL_BENCHMARKS:
            # Fallback benchmark for unspecified grain crops with documented uncertainty
            # If no defensible threshold exists, flag for review rather than inventing one.
            benchmark = CropRemovalBenchmark(
                crop_name=crop_name.capitalize(),
                n_kg_per_ton=22.0,
                p_elemental_kg_per_ton=3.5,
                k_elemental_kg_per_ton=20.0,
                bnf_nitrogen_fraction=0.0,
                straw_stover_ratio=1.0,
                straw_k_retention_fraction=0.70,
                source_citation="Generic Cereal Proxy (ICAR General Averages)",
                max_plausible_yield_tons_ha=None,
                yield_basis="Unspecified Crop Product",
                yield_source_citation="No defensible crop-specific yield threshold available; human review required"
            )
            review_required = True
            review_flags.append(
                f"FLAG_UNSUPPORTED_CROP_NO_DEFENSIBLE_THRESHOLD: Unrecognized crop '{crop_name}'; "
                "generic cereal proxy removal applied; agronomist review required to verify harvest yield."
            )
            assumptions = [
                f"Crop '{crop_name}' not in verified lookup; used generic cereal proxy (22 kg N, 3.5 kg P, 20 kg K per ton).",
                "Uncertainty widened by ±30% due to proxy estimation.",
                "REVIEW REQUIRED: No defensible yield threshold exists for this crop; pending human agronomist verification."
            ]
            uncertainty_mult = 1.30
        else:
            benchmark = CROP_REMOVAL_BENCHMARKS[key]
            assumptions = [
                f"Applied benchmark for {benchmark.crop_name} ({benchmark.source_citation}).",
                f"Yield reported: {yield_tons_ha} t/ha ({benchmark.yield_basis})."
            ]
            uncertainty_mult = 1.0

            # Crop-specific upper plausibility check
            if benchmark.max_plausible_yield_tons_ha is not None and yield_tons_ha > benchmark.max_plausible_yield_tons_ha:
                review_required = True
                flag_msg = (
                    f"SUSPICIOUS_HIGH_YIELD: Reported yield of {yield_tons_ha} t/ha exceeds maximum plausible "
                    f"agronomic threshold ({benchmark.max_plausible_yield_tons_ha} t/ha for {benchmark.crop_name}). "
                    f"Preserved raw reported value; human review required."
                )
                review_flags.append(flag_msg)
                assumptions.append(
                    f"WARNING: Reported yield {yield_tons_ha} t/ha exceeds maximum plausible bound "
                    f"({benchmark.max_plausible_yield_tons_ha} t/ha based on {benchmark.yield_source_citation}). "
                    "Calculation preserves raw reported value without silent clamping, but requires agronomic verification."
                )

        # 1. Nitrogen removal (accounting for biological N2 fixation)
        n_removed = benchmark.net_soil_n_kg_per_ton * yield_tons_ha
        if benchmark.bnf_nitrogen_fraction > 0:
            assumptions.append(
                f"Legume biological N2 fixation credited: {benchmark.bnf_nitrogen_fraction*100:.0f}% of N derived from air."
            )

        # 2. Phosphorus removal
        p_removed = benchmark.p_elemental_kg_per_ton * yield_tons_ha

        # 3. Potassium removal (accounting for residue retention)
        if residue_retained:
            # If straw is left on field, ~70% of plant K is returned to the soil surface
            k_retention = benchmark.straw_k_retention_fraction
            k_removed = benchmark.k_elemental_kg_per_ton * yield_tons_ha * (1.0 - k_retention)
            assumptions.append(
                f"Residue retained on field: {k_retention*100:.0f}% of vegetative K returned to soil surface."
            )
        else:
            k_removed = benchmark.k_elemental_kg_per_ton * yield_tons_ha
            assumptions.append("All crop residue (grain + straw/stover) removed from field.")

        # Estimate estimation variance (typically ±15% on field trials, higher on proxy)
        unc_n = round(n_removed * 0.15 * uncertainty_mult, 2)
        unc_p = round(p_removed * 0.15 * uncertainty_mult, 2)
        unc_k = round(k_removed * 0.20 * uncertainty_mult, 2)

        return NutrientFluxEvent(
            event_id=event_id,
            event_date=event_date,
            event_type="CROP_DEPLETION",
            description=f"Crop Harvest Removal: {benchmark.crop_name} ({yield_tons_ha} t/ha)",
            delta_n_kg_ha=-round(n_removed, 2),
            delta_p_elemental_kg_ha=-round(p_removed, 2),
            delta_k_elemental_kg_ha=-round(k_removed, 2),
            uncertainty_n_kg_ha=unc_n,
            uncertainty_p_kg_ha=unc_p,
            uncertainty_k_kg_ha=unc_k,
            calculation_method="Mass Removal = Yield (t/ha) * Nutrient Extraction Rate (kg/t)",
            assumptions=assumptions,
            source_citation=benchmark.source_citation,
            provenance=ProvenanceType.FARMER_RECORDED,
            raw_reported_yield_tons_ha=yield_tons_ha,
            review_required=review_required,
            review_flags=review_flags
        )

    @classmethod
    def calculate_fertilizer_input(
        cls,
        fertilizer_name: str,
        application_rate_kg_ha: float,
        event_date: str,
        event_id: str = "FERTILIZER_INPUT"
    ) -> NutrientFluxEvent:
        """
        Calculates N, P, K addition for mineral fertilizer or organic manure application.
        """
        if application_rate_kg_ha <= 0:
            raise ValueError(f"Fertilizer application rate must be strictly positive: {application_rate_kg_ha}")

        key = fertilizer_name.strip().lower()
        if key not in FERTILIZER_GRADE_BENCHMARKS:
            raise KeyError(
                f"Unrecognized fertilizer grade: '{fertilizer_name}'. "
                f"Supported grades: {list(FERTILIZER_GRADE_BENCHMARKS.keys())}"
            )

        grade = FERTILIZER_GRADE_BENCHMARKS[key]
        assumptions = [
            f"Applied FCO benchmark for {grade.fertilizer_name} ({grade.source_citation}).",
            f"Gross applied rate: {application_rate_kg_ha} kg/ha."
        ]

        # Calculate nutrient additions
        n_added = application_rate_kg_ha * grade.n_fraction * grade.first_year_n_availability
        p_added = application_rate_kg_ha * grade.p_elemental_fraction
        k_added = application_rate_kg_ha * grade.k_elemental_fraction

        if grade.is_organic and grade.first_year_n_availability < 1.0:
            assumptions.append(
                f"Organic mineralization kinetics applied: {grade.first_year_n_availability*100:.0f}% of total N available in Year 1."
            )

        # Standard measurement uncertainty for application uniformity (~10%)
        unc_n = round(n_added * 0.10, 2)
        unc_p = round(p_added * 0.10, 2)
        unc_k = round(k_added * 0.10, 2)

        event_type = "MANURE_ADDITION" if grade.is_organic else "FERTILIZER_ADDITION"

        return NutrientFluxEvent(
            event_id=event_id,
            event_date=event_date,
            event_type=event_type,
            description=f"Nutrient Addition: {grade.fertilizer_name} ({application_rate_kg_ha} kg/ha)",
            delta_n_kg_ha=round(n_added, 2),
            delta_p_elemental_kg_ha=round(p_added, 2),
            delta_k_elemental_kg_ha=round(k_added, 2),
            uncertainty_n_kg_ha=unc_n,
            uncertainty_p_kg_ha=unc_p,
            uncertainty_k_kg_ha=unc_k,
            calculation_method="Mass Addition = Applied Rate (kg/ha) * Nutrient Grade Fraction",
            assumptions=assumptions,
            source_citation=grade.source_citation,
            provenance=ProvenanceType.FARMER_RECORDED
        )

    @classmethod
    def compile_cumulative_ledger(
        cls,
        plot_id: str,
        start_date: str,
        end_date: str,
        flux_events: List[NutrientFluxEvent],
        known_unrecorded_days: int = 0,
        unrecorded_crop_cycles: bool = False
    ) -> CumulativeMassBalanceLedger:
        """
        Compiles the cumulative multi-year ledger across all dated events,
        propagates uncertainties in quadrature, and flags data gaps.
        """
        # Filter events within date window
        window_events = [
            e for e in flux_events
            if start_date <= e.event_date <= end_date
        ]

        gross_n_add = 0.0
        gross_p_add = 0.0
        gross_k_add = 0.0
        gross_n_rem = 0.0
        gross_p_rem = 0.0
        gross_k_rem = 0.0

        var_n = 0.0
        var_p = 0.0
        var_k = 0.0

        for e in window_events:
            if e.delta_n_kg_ha > 0: gross_n_add += e.delta_n_kg_ha
            else: gross_n_rem += abs(e.delta_n_kg_ha)

            if e.delta_p_elemental_kg_ha > 0: gross_p_add += e.delta_p_elemental_kg_ha
            else: gross_p_rem += abs(e.delta_p_elemental_kg_ha)

            if e.delta_k_elemental_kg_ha > 0: gross_k_add += e.delta_k_elemental_kg_ha
            else: gross_k_rem += abs(e.delta_k_elemental_kg_ha)

            # Accumulate variance for independent event uncertainties
            var_n += (e.uncertainty_n_kg_ha ** 2)
            var_p += (e.uncertainty_p_kg_ha ** 2)
            var_k += (e.uncertainty_k_kg_ha ** 2)

        # Calculate days elapsed
        try:
            d_start = datetime.strptime(start_date, "%Y-%m-%d")
            d_end = datetime.strptime(end_date, "%Y-%m-%d")
            days_elapsed = max(0, (d_end - d_start).days)
        except Exception:
            days_elapsed = 0

        # Calculate input coverage and penalty for missing events
        flags = []
        coverage = 1.0

        # Check for suspicious events requiring agronomic review
        has_suspicious_events = False
        for e in window_events:
            if getattr(e, 'review_required', False):
                has_suspicious_events = True
                for rf in getattr(e, 'review_flags', []):
                    if rf not in flags:
                        flags.append(rf)

        if has_suspicious_events:
            flags.append(
                "FLAG_UNCONFIRMED_HIGH_YIELD_IN_LEDGER: One or more harvest events in this ledger "
                "have unconfirmed high yields requiring human review."
            )

        if unrecorded_crop_cycles:
            flags.append("FLAG_UNRECORDED_CROPS: Plot underwent crop cultivation without logged harvest yield.")
            coverage *= 0.60
            # Expand uncertainty when crops were grown without records
            var_n += (40.0 ** 2)
            var_p += (8.0 ** 2)
            var_k += (35.0 ** 2)

        if known_unrecorded_days > 180:
            flags.append(f"FLAG_DATA_GAP: Extended gap of {known_unrecorded_days} days without any recorded farm activities.")
            coverage *= max(0.20, 1.0 - (known_unrecorded_days / 730.0))
            # Time-dependent drift uncertainty (mineralization / leaching drift)
            drift_n = 0.05 * known_unrecorded_days
            var_n += (drift_n ** 2)

        if len(window_events) == 0:
            flags.append("FLAG_ZERO_EVENTS: No fertilizer or crop events were logged between dates.")
            coverage = 0.10

        net_n = round(gross_n_add - gross_n_rem, 2)
        net_p = round(gross_p_add - gross_p_rem, 2)
        net_k = round(gross_k_add - gross_k_rem, 2)

        unc_n = round(math.sqrt(var_n), 2)
        unc_p = round(math.sqrt(var_p), 2)
        unc_k = round(math.sqrt(var_k), 2)

        return CumulativeMassBalanceLedger(
            plot_id=plot_id,
            start_date=start_date,
            end_date=end_date,
            days_elapsed=days_elapsed,
            gross_n_added_kg_ha=round(gross_n_add, 2),
            gross_p_added_kg_ha=round(gross_p_add, 2),
            gross_k_added_kg_ha=round(gross_k_add, 2),
            gross_n_removed_kg_ha=round(gross_n_rem, 2),
            gross_p_removed_kg_ha=round(gross_p_rem, 2),
            gross_k_removed_kg_ha=round(gross_k_rem, 2),
            net_balance_n_kg_ha=net_n,
            net_balance_p_kg_ha=net_p,
            net_balance_k_kg_ha=net_k,
            balance_uncertainty_n_kg_ha=unc_n,
            balance_uncertainty_p_kg_ha=unc_p,
            balance_uncertainty_k_kg_ha=unc_k,
            has_unrecorded_crop_cycles=unrecorded_crop_cycles,
            has_unrecorded_fertilizer_periods=(known_unrecorded_days > 180),
            unrecorded_days_estimate=known_unrecorded_days,
            input_coverage_score=round(coverage, 2),
            data_quality_flags=flags,
            has_unreviewed_suspicious_events=has_suspicious_events
        )

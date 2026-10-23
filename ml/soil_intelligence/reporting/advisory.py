"""
Agronomic Soil Advisory & Educational Guidance Engine
=====================================================
Generates evidence-backed educational guidance based on verified soil testing
standards (ICAR / Tandon 2004 / Muhr et al. 1965).

CRITICAL SAFEGUARDS:
  1. Educational guidance is strictly separated from site-specific prescriptions.
  2. Fertilizer dosages are NEVER calculated directly from mass-balance ledgers.
  3. No unsupported crop-specific chemical doses are generated without validated ground truth.
  4. Requires consultation with certified district agronomists or Krishi Vigyan Kendra (KVK).
  5. Explains freshness and gap issues using physical/biological mechanisms rather than arbitrary warnings.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Any


class NutrientTier(str, Enum):
    VERY_LOW = "VERY_LOW"
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    VERY_HIGH = "VERY_HIGH"
    NOT_DETERMINED = "NOT_DETERMINED"


class ReactionTier(str, Enum):
    STRONGLY_ACIDIC = "STRONGLY_ACIDIC"       # < 5.5
    MODERATELY_ACIDIC = "MODERATELY_ACIDIC"   # 5.5 - 6.5
    NEUTRAL = "NEUTRAL"                       # 6.5 - 7.5
    MODERATELY_ALKALINE = "MODERATELY_ALKALINE" # 7.5 - 8.5
    STRONGLY_ALKALINE = "STRONGLY_ALKALINE"   # > 8.5
    NOT_DETERMINED = "NOT_DETERMINED"


class SalinityTier(str, Enum):
    NORMAL = "NORMAL"                         # < 1.0 dS/m
    CRITICAL_FOR_SEEDLINGS = "CRITICAL"       # 1.0 - 2.0 dS/m
    INJURIOUS_SALINE = "INJURIOUS"            # > 2.0 dS/m
    NOT_DETERMINED = "NOT_DETERMINED"


class OrganicCarbonTier(str, Enum):
    LOW = "LOW"                               # < 0.50%
    MEDIUM = "MEDIUM"                         # 0.50% - 0.75%
    HIGH = "HIGH"                             # > 0.75%
    NOT_DETERMINED = "NOT_DETERMINED"


@dataclass
class AgronomicAdvisoryItem:
    parameter: str
    reported_value: Optional[float]
    reported_unit: str
    normalized_value_kg_ha: Optional[float]
    tier: str
    status_label: str
    educational_interpretation: str
    management_considerations: List[str]
    scientific_reference: str
    guidance_scope: str = "GENERAL_EDUCATIONAL_GUIDANCE"
    is_provisional: bool = False
    provisional_reason: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "parameter": self.parameter,
            "reported_value": self.reported_value,
            "reported_unit": self.reported_unit,
            "normalized_value_kg_ha": self.normalized_value_kg_ha,
            "tier": self.tier,
            "status_label": self.status_label,
            "educational_interpretation": self.educational_interpretation,
            "management_considerations": self.management_considerations,
            "scientific_reference": self.scientific_reference,
            "guidance_scope": self.guidance_scope,
            "is_provisional": self.is_provisional,
            "provisional_reason": self.provisional_reason,
        }


@dataclass
class SoilAdvisoryBundle:
    plot_id: str
    has_valid_lab_test: bool
    nitrogen_advisory: Optional[AgronomicAdvisoryItem] = None
    phosphorus_advisory: Optional[AgronomicAdvisoryItem] = None
    potassium_advisory: Optional[AgronomicAdvisoryItem] = None
    reaction_advisory: Optional[AgronomicAdvisoryItem] = None
    salinity_advisory: Optional[AgronomicAdvisoryItem] = None
    organic_carbon_advisory: Optional[AgronomicAdvisoryItem] = None
    general_recommendations: List[str] = field(default_factory=list)
    agronomic_disclaimer: str = (
        "AGRONOMIC ADVISORY MANDATE: The guidance provided in this report is educational and "
        "informational based on standard ICAR soil fertility classifications. It DOES NOT "
        "constitute an empirical chemical prescription. Fertilizer scheduling must account for "
        "crop variety, soil moisture, irrigation schedule, and local agronomic recommendations. "
        "Consult your local Krishi Vigyan Kendra (KVK) or State Agricultural University agronomist."
    )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "plot_id": self.plot_id,
            "has_valid_lab_test": self.has_valid_lab_test,
            "nitrogen_advisory": self.nitrogen_advisory.to_dict() if self.nitrogen_advisory else None,
            "phosphorus_advisory": self.phosphorus_advisory.to_dict() if self.phosphorus_advisory else None,
            "potassium_advisory": self.potassium_advisory.to_dict() if self.potassium_advisory else None,
            "reaction_advisory": self.reaction_advisory.to_dict() if self.reaction_advisory else None,
            "salinity_advisory": self.salinity_advisory.to_dict() if self.salinity_advisory else None,
            "organic_carbon_advisory": self.organic_carbon_advisory.to_dict() if self.organic_carbon_advisory else None,
            "general_recommendations": self.general_recommendations,
            "agronomic_disclaimer": self.agronomic_disclaimer,
        }


class AgronomicAdvisoryEngine:
    """
    Evaluates soil parameters against national ICAR soil fertility benchmarks
    and generates scientifically validated educational guidance.
    """

    # ICAR Benchmark Thresholds (elemental kg/ha in 0-15 cm plow layer)
    N_LOW_MAX = 280.0
    N_MEDIUM_MAX = 560.0

    # Olsen P: elemental P (P2O5: Low < 23 kg/ha, Med 23-56 kg/ha, High > 56 kg/ha)
    P_ELEMENTAL_LOW_MAX = 10.0      # ~22.9 kg P2O5/ha
    P_ELEMENTAL_MEDIUM_MAX = 24.4   # ~55.9 kg P2O5/ha

    # NH4OAc K: elemental K (K2O: Low < 144 kg/ha, Med 144-336 kg/ha, High > 336 kg/ha)
    K_ELEMENTAL_LOW_MAX = 119.5     # ~144 kg K2O/ha
    K_ELEMENTAL_MEDIUM_MAX = 278.9  # ~336 kg K2O/ha

    @classmethod
    def classify_nitrogen(cls, n_kg_ha: Optional[float], reported_val: Optional[float] = None, reported_unit: str = "kg/ha") -> AgronomicAdvisoryItem:
        if n_kg_ha is None:
            return AgronomicAdvisoryItem(
                parameter="Available Nitrogen (N)",
                reported_value=reported_val,
                reported_unit=reported_unit,
                normalized_value_kg_ha=None,
                tier=NutrientTier.NOT_DETERMINED.value,
                status_label="Not Available",
                educational_interpretation="Nitrogen concentration was not reported in the laboratory test.",
                management_considerations=["Conduct Alkaline Permanganate test to determine available mineral nitrogen."],
                scientific_reference="Subbiah & Asija (1956) Alkaline Permanganate Protocol"
            )

        if n_kg_ha < cls.N_LOW_MAX:
            tier = NutrientTier.LOW
            label = "Low (< 280 kg/ha)"
            interpretation = (
                f"Available nitrogen ({n_kg_ha:.1f} kg/ha) is in the LOW fertility tier. "
                "Cereal and cash crops in this tier typically demonstrate strong yield responsiveness "
                "to balanced nitrogen application and organic manure incorporation."
            )
            considerations = [
                "Consider split application of mineral nitrogen (basal + top dressings) to reduce leaching and volatilization.",
                "Incorporate leguminous green manures or pulses to augment biological N2 fixation.",
                "Integrate compost or farmyard manure (FYM) to enhance native soil microbial nitrogen cycling."
            ]
        elif n_kg_ha <= cls.N_MEDIUM_MAX:
            tier = NutrientTier.MEDIUM
            label = "Medium (280 - 560 kg/ha)"
            interpretation = (
                f"Available nitrogen ({n_kg_ha:.1f} kg/ha) is in the MEDIUM fertility tier. "
                "The soil maintains standard baseline nitrogen reserves adequate for average crop maintenance."
            )
            considerations = [
                "Apply recommended maintenance nitrogen rates suited to the targeted crop yield.",
                "Avoid excessive early nitrogen applications to prevent vegetative lodging and pest susceptibility."
            ]
        else:
            tier = NutrientTier.HIGH
            label = "High (> 560 kg/ha)"
            interpretation = (
                f"Available nitrogen ({n_kg_ha:.1f} kg/ha) is in the HIGH fertility tier. "
                "The soil holds substantial mineralized nitrogen reserves."
            )
            considerations = [
                "Avoid over-application of synthetic nitrogen fertilizers to prevent nitrate runoff and economic waste.",
                "Monitor crop vigor; excessive nitrogen may delay reproductive maturity and increase disease vulnerability."
            ]

        return AgronomicAdvisoryItem(
            parameter="Available Nitrogen (N)",
            reported_value=reported_val if reported_val is not None else n_kg_ha,
            reported_unit=reported_unit,
            normalized_value_kg_ha=n_kg_ha,
            tier=tier.value,
            status_label=label,
            educational_interpretation=interpretation,
            management_considerations=considerations,
            scientific_reference="ICAR Standard Soil Fertility Classification (Subbiah & Asija 1956)"
        )

    @classmethod
    def classify_phosphorus(cls, p_kg_ha: Optional[float], reported_val: Optional[float] = None, reported_unit: str = "kg/ha") -> AgronomicAdvisoryItem:
        if p_kg_ha is None:
            return AgronomicAdvisoryItem(
                parameter="Available Phosphorus (P)",
                reported_value=reported_val,
                reported_unit=reported_unit,
                normalized_value_kg_ha=None,
                tier=NutrientTier.NOT_DETERMINED.value,
                status_label="Not Available",
                educational_interpretation="Phosphorus concentration was not reported.",
                management_considerations=["Olsen NaHCO3 extraction recommended for neutral to calcareous soils."],
                scientific_reference="Olsen et al. (1954)"
            )

        if p_kg_ha < cls.P_ELEMENTAL_LOW_MAX:
            tier = NutrientTier.LOW
            label = "Low (< 10 kg elemental P/ha or < 23 kg P2O5/ha)"
            interpretation = (
                f"Available phosphorus ({p_kg_ha:.1f} kg elemental P/ha) is in the LOW fertility tier. "
                "Phosphorus deficiency severely restricts root development and early seedling vigor."
            )
            considerations = [
                "Apply phosphatic fertilizers as basal placement close to seed rows to counter fixation.",
                "In alkaline/calcareous soils, consider phosphorus-solubilizing biofertilizers (PSB).",
                "Maintain adequate soil moisture during early root establishment."
            ]
        elif p_kg_ha <= cls.P_ELEMENTAL_MEDIUM_MAX:
            tier = NutrientTier.MEDIUM
            label = "Medium (10 - 24.4 kg elemental P/ha or 23 - 56 kg P2O5/ha)"
            interpretation = (
                f"Available phosphorus ({p_kg_ha:.1f} kg elemental P/ha) is in the MEDIUM fertility tier."
            )
            considerations = [
                "Apply maintenance phosphorus equivalent to expected crop harvest removal.",
                "Ensure balanced N:P ratio to support root and shoot development."
            ]
        else:
            tier = NutrientTier.HIGH
            label = "High (> 24.4 kg elemental P/ha or > 56 kg P2O5/ha)"
            interpretation = (
                f"Available phosphorus ({p_kg_ha:.1f} kg elemental P/ha) is in the HIGH fertility tier."
            )
            considerations = [
                "Phosphatic fertilization rates can be moderated to avoid zinc deficiency induced by high P.",
                "Soil phosphorus pools have limited leaching loss but can build up under continuous heavy application."
            ]

        return AgronomicAdvisoryItem(
            parameter="Available Phosphorus (P)",
            reported_value=reported_val if reported_val is not None else p_kg_ha,
            reported_unit=reported_unit,
            normalized_value_kg_ha=p_kg_ha,
            tier=tier.value,
            status_label=label,
            educational_interpretation=interpretation,
            management_considerations=considerations,
            scientific_reference="Olsen 0.5M NaHCO3 Extraction Protocol (Olsen et al. 1954; Muhr et al. 1965)"
        )

    @classmethod
    def classify_potassium(cls, k_kg_ha: Optional[float], reported_val: Optional[float] = None, reported_unit: str = "kg/ha") -> AgronomicAdvisoryItem:
        if k_kg_ha is None:
            return AgronomicAdvisoryItem(
                parameter="Available Potassium (K)",
                reported_value=reported_val,
                reported_unit=reported_unit,
                normalized_value_kg_ha=None,
                tier=NutrientTier.NOT_DETERMINED.value,
                status_label="Not Available",
                educational_interpretation="Potassium concentration was not reported.",
                management_considerations=["Neutral 1N ammonium acetate extraction recommended."],
                scientific_reference="Hanway & Heidel (1952)"
            )

        if k_kg_ha < cls.K_ELEMENTAL_LOW_MAX:
            tier = NutrientTier.LOW
            label = "Low (< 120 kg elemental K/ha or < 144 kg K2O/ha)"
            interpretation = (
                f"Available potassium ({k_kg_ha:.1f} kg elemental K/ha) is in the LOW fertility tier. "
                "Low potassium reduces plant drought tolerance, stem strength, and grain filling."
            )
            considerations = [
                "Apply potash (MOP) to satisfy crop demand, particularly in potassium-demanding crops (e.g. Sugarcane, Cotton, Maize).",
                "Retain cereal crop residues on field to recycle up to 75% of vegetative potassium back to the soil."
            ]
        elif k_kg_ha <= cls.K_ELEMENTAL_MEDIUM_MAX:
            tier = NutrientTier.MEDIUM
            label = "Medium (120 - 279 kg elemental K/ha or 144 - 336 kg K2O/ha)"
            interpretation = (
                f"Available potassium ({k_kg_ha:.1f} kg elemental K/ha) is in the MEDIUM fertility tier."
            )
            considerations = [
                "Apply maintenance potash rates to match crop export.",
                "In heavy clay vertisols, monitor non-exchangeable K reserves."
            ]
        else:
            tier = NutrientTier.HIGH
            label = "High (> 279 kg elemental K/ha or > 336 kg K2O/ha)"
            interpretation = (
                f"Available potassium ({k_kg_ha:.1f} kg elemental K/ha) is in the HIGH fertility tier. "
                "Black cotton soils (Vertisols) typically exhibit strong native potassium reserves."
            )
            considerations = [
                "Potash fertilization can be safely reduced or skipped for short-duration crops.",
                "Ensure balanced nutrition with calcium and magnesium to prevent cationic competition."
            ]

        return AgronomicAdvisoryItem(
            parameter="Available Potassium (K)",
            reported_value=reported_val if reported_val is not None else k_kg_ha,
            reported_unit=reported_unit,
            normalized_value_kg_ha=k_kg_ha,
            tier=tier.value,
            status_label=label,
            educational_interpretation=interpretation,
            management_considerations=considerations,
            scientific_reference="Neutral 1N Ammonium Acetate Protocol (Hanway & Heidel 1952)"
        )

    @classmethod
    def classify_ph(cls, ph: Optional[float]) -> Optional[AgronomicAdvisoryItem]:
        if ph is None:
            return None
        is_prov = False
        prov_reason = None
        if ph < 3.5 or ph > 10.5:
            is_prov = True
            prov_reason = f"Reported pH {ph:.2f} is outside standard agricultural cultivation bounds (<3.5 or >10.5); provisional pending laboratory re-test."

        if ph < 5.5:
            tier = ReactionTier.STRONGLY_ACIDIC
            label = "Strongly Acidic (< 5.5)"
            interp = f"Soil reaction (pH {ph:.2f}) is strongly acidic, which restricts phosphorus and molybdenum availability."
            cons = ["Agricultural liming (calcium carbonate) may be recommended following buffer capacity testing."]
        elif ph < 6.5:
            tier = ReactionTier.MODERATELY_ACIDIC
            label = "Moderately Acidic (5.5 - 6.5)"
            interp = f"Soil reaction (pH {ph:.2f}) is moderately acidic. Favorable for most field crops."
            cons = ["Monitor secondary nutrient availability."]
        elif ph <= 7.5:
            tier = ReactionTier.NEUTRAL
            label = "Neutral (6.5 - 7.5)"
            interp = f"Soil reaction (pH {ph:.2f}) is in the optimal NEUTRAL range for nutrient assimilation and biological activity."
            cons = ["Optimal range for nutrient uptake; no corrective soil amendments required."]
        elif ph <= 8.5:
            tier = ReactionTier.MODERATELY_ALKALINE
            label = "Moderately Alkaline (7.5 - 8.5)"
            interp = f"Soil reaction (pH {ph:.2f}) is moderately alkaline (typical for calcareous Vertisols of Central India)."
            cons = ["Free calcium carbonate may fix applied soluble phosphates into insoluble calcium phosphates.",
                    "Incorporate organic manures (FYM) to generate organic acids that buffer root-zone pH."]
        else:
            tier = ReactionTier.STRONGLY_ALKALINE
            label = "Strongly Alkaline (> 8.5)"
            interp = f"Soil reaction (pH {ph:.2f}) is strongly alkaline. Risk of micronutrient (Zn, Fe, Mn) deficiencies."
            cons = ["Gypsum application and drainage management may be required if high exchangeable sodium is present.",
                    "Foliar application of chelated micronutrients may be beneficial."]

        return AgronomicAdvisoryItem(
            parameter="Soil Reaction (pH)",
            reported_value=ph,
            reported_unit="pH scale",
            normalized_value_kg_ha=None,
            tier=tier.value,
            status_label=label,
            educational_interpretation=interp,
            management_considerations=cons,
            scientific_reference=(
                "Analytical Protocol: Standard 1:2.5 Soil-Water Suspension Potentiometric Method (Jackson 1973 §3). "
                "Reaction Tier Thresholds: Strongly Acidic (<5.5), Moderately Acidic (5.5-6.5), Neutral (6.5-7.5), "
                "Moderately Alkaline (7.5-8.5), Strongly Alkaline (>8.5) (USDA-NRCS Soil Survey Manual 2017 Table 3-3; "
                "Muhr et al. 1965 / ICAR Soil Testing Standards)."
            ),
            guidance_scope="GENERAL_EDUCATIONAL_GUIDANCE",
            is_provisional=is_prov,
            provisional_reason=prov_reason
        )

    @classmethod
    def generate_plot_advisory_bundle(
        cls,
        plot_id: str,
        n_kg_ha: Optional[float] = None,
        p_kg_ha: Optional[float] = None,
        k_kg_ha: Optional[float] = None,
        ph: Optional[float] = None,
        ec_ds_m: Optional[float] = None,
        oc_pct: Optional[float] = None,
        reported_n: Optional[float] = None,
        reported_p: Optional[float] = None,
        reported_k: Optional[float] = None,
        reported_unit_n: str = "kg/ha",
        reported_unit_p: str = "kg/ha",
        reported_unit_k: str = "kg/ha"
    ) -> SoilAdvisoryBundle:
        """
        Compiles an integrated educational advisory bundle across all available parameters.
        """
        has_lab = any(v is not None for v in [n_kg_ha, p_kg_ha, k_kg_ha, ph, oc_pct])

        n_adv = cls.classify_nitrogen(n_kg_ha, reported_n, reported_unit_n)
        p_adv = cls.classify_phosphorus(p_kg_ha, reported_p, reported_unit_p)
        k_adv = cls.classify_potassium(k_kg_ha, reported_k, reported_unit_k)
        ph_adv = cls.classify_ph(ph)

        general_recs = [
            "Maintain integrated nutrient management (INM) combining organic manures with targeted mineral fertilization.",
            "Recycle crop residues (stover/straw) on field to preserve potassium reserves and enhance soil organic matter.",
            "Do NOT calculate commercial fertilizer dosages directly from simple mass-balance ledgers.",
            "Consult district Krishi Vigyan Kendra (KVK) or local university agronomist for customized crop prescriptions."
        ]

        return SoilAdvisoryBundle(
            plot_id=plot_id,
            has_valid_lab_test=has_lab,
            nitrogen_advisory=n_adv,
            phosphorus_advisory=p_adv,
            potassium_advisory=k_adv,
            reaction_advisory=ph_adv,
            general_recommendations=general_recs
        )

"""
Fertilizer & Soil Nutrient Advisory Orchestration Service.
Integrates real ML inference, commercial formulation calculations, local store discovery, and safeguards.
"""

import logging
from typing import Any, Dict, List
from .model_adapter import fertilizer_model_adapter
from .schemas import (
    CommercialFertilizerRecommendation,
    FertilizerAdvisoryResponse,
    FertilizerInput,
    NutrientRequirement,
)
from .store_service import build_amazon_discovery_links, find_matching_stores

logger = logging.getLogger(__name__)


class FertilizerAdvisoryService:
    """Orchestrates agronomic ML prediction, commercial dosage calculation, and local store matching."""

    def __init__(self):
        self.adapter = fertilizer_model_adapter

    def generate_advisory(self, payload: FertilizerInput) -> FertilizerAdvisoryResponse:
        warnings: List[str] = []

        # 1. Execute Real ML Model Inference
        inference_out = self.adapter.predict(
            crop_name=payload.crop_name,
            target_yield_kg_ha=payload.target_yield,
            field_size_ha=payload.field_size,
            ph=payload.ph,
            organic_carbon=payload.organic_carbon,
            total_nitrogen=payload.total_nitrogen,
            available_phosphorus=payload.available_phosphorus,
            exchangeable_potassium=payload.exchangeable_potassium,
        )

        preds = inference_out["predictions"]
        warnings.extend(inference_out["warnings"])

        # 2. Extract Nutrient Needs
        n_need = preds.get("Nitrogen (N) Need", 0.0)
        p_need = preds.get("Phosphorus (P2O5) Need", 0.0)
        k_need = preds.get("Potassium (K2O) Need", 0.0)
        om_need = preds.get("Organic Matter Need", 0.0)
        lime_need = preds.get("Lime Need", 0.0)

        nutrient_reqs: List[NutrientRequirement] = [
            NutrientRequirement(
                nutrient="Nitrogen (N)",
                quantity=n_need,
                unit="kg/ha",
                application_stage="Split: 50% Basal + 50% Top-dressing at vegetative stage",
                description="Promotes vegetative biomass, leaf canopy expansion, and photosynthetic capacity."
            ),
            NutrientRequirement(
                nutrient="Phosphorus (P2O5)",
                quantity=p_need,
                unit="kg/ha",
                application_stage="100% Basal at sowing / transplanting",
                description="Stimulates early root architecture, vigorous establishment, and floral initiation."
            ),
            NutrientRequirement(
                nutrient="Potassium (K2O)",
                quantity=k_need,
                unit="kg/ha",
                application_stage="Basal with split at flowering for stress tolerance",
                description="Enhances osmoregulation, disease tolerance, stem strength, and fruit/grain filling."
            ),
        ]

        if om_need > 0:
            nutrient_reqs.append(
                NutrientRequirement(
                    nutrient="Organic Matter / Compost",
                    quantity=om_need,
                    unit="kg/ha",
                    application_stage="Pre-sowing field incorporation (2-3 weeks before sowing)",
                    description="Improves microbial diversity, soil cation exchange capacity (CEC), and water retention."
                )
            )

        if payload.ph < 6.0 and lime_need > 0:
            nutrient_reqs.append(
                NutrientRequirement(
                    nutrient="Agricultural Lime (CaCO3)",
                    quantity=lime_need,
                    unit="kg/ha",
                    application_stage="Broadcast and incorporate 4 weeks before sowing",
                    description="Neutralizes soil acidity and replenishes available calcium."
                )
            )

        # 3. Calculate Indian Commercial Fertilizer Formulations
        commercial: List[CommercialFertilizerRecommendation] = []
        target_commercial_names: List[str] = []

        # DAP provides both P2O5 (46%) and N (18%)
        if p_need > 0:
            dap_kg = round(p_need / 0.46, 1)
            dap_bags = round(dap_kg / 50.0, 1)
            commercial.append(
                CommercialFertilizerRecommendation(
                    fertilizer_name="Di-Ammonium Phosphate (DAP)",
                    grade="18-46-0",
                    dose_kg_ha=dap_kg,
                    bags_50kg_per_ha=dap_bags,
                    application_timing="Apply as basal placement at seed depth during sowing."
                )
            )
            target_commercial_names.append("Di-Ammonium Phosphate (DAP)")
            # Subtract N provided by DAP: 18% of DAP quantity
            n_supplied_by_dap = dap_kg * 0.18
            remaining_n = max(0.0, n_need - n_supplied_by_dap)
        else:
            remaining_n = n_need

        # Urea provides N (46%)
        if remaining_n > 0:
            urea_kg = round(remaining_n / 0.46, 1)
            urea_bags = round(urea_kg / 45.0, 1)  # Standard neem coated bag is 45kg in India
            commercial.append(
                CommercialFertilizerRecommendation(
                    fertilizer_name="Neem Coated Urea",
                    grade="46% N",
                    dose_kg_ha=urea_kg,
                    bags_50kg_per_ha=urea_bags,
                    application_timing="Apply in 2 equal splits: 50% at 30 days and 50% at flowering stage."
                )
            )
            target_commercial_names.append("Neem Coated Urea")

        # MOP provides K2O (60%)
        if k_need > 0:
            mop_kg = round(k_need / 0.60, 1)
            mop_bags = round(mop_kg / 50.0, 1)
            commercial.append(
                CommercialFertilizerRecommendation(
                    fertilizer_name="Muriate of Potash (MOP)",
                    grade="0-0-60",
                    dose_kg_ha=mop_kg,
                    bags_50kg_per_ha=mop_bags,
                    application_timing="Apply as basal dressing or split with irrigation."
                )
            )
            target_commercial_names.append("Muriate of Potash (MOP)")

        # 4. Disease Context Separation Notice
        disease_notice = None
        if payload.disease_context:
            disease_notice = (
                f"Notice: This fertilizer plan addresses soil nutrient status and is independent "
                f"of foliar disease conditions ('{payload.disease_context}'). Fertilizers optimize "
                f"plant vigor but do not cure fungal or viral infections. Maintain separate IPM protocols."
            )

        # 5. Local Demo Store Discovery
        stores = find_matching_stores(
            locality=payload.locality,
            pin_code=payload.pin_code,
            district=payload.district,
            recommended_fertilizers=target_commercial_names,
        )

        # 6. Amazon.in Discovery Links
        amazon_links = build_amazon_discovery_links(target_commercial_names)

        # 7. Validation / Regional Notice
        validation_notice = (
            "EXPERIMENTAL / UNVALIDATED STATUS: This advisory is generated by a multi-output "
            "Random Forest machine learning model trained on agricultural soil survey data. "
            "It has not been calibrated or field-validated against ICAR / Dr. PDKV Akola soil test "
            "crop response (STCR) calibrations for Maharashtra vertisols. Do not treat numerical dosages "
            "as absolute legal specifications. Cross-reference with your official Soil Health Card (SHC) "
            "or local Krishi Vigyan Kendra (KVK) agronomist before purchase."
        )

        return FertilizerAdvisoryResponse(
            status="success",
            crop=payload.crop_name,
            field_size_ha=payload.field_size,
            target_yield_kg_ha=payload.target_yield,
            model_identifier=self.adapter.model_identifier if hasattr(self.adapter, "model_identifier") else "DNgigi/FertiliserApplication",
            model_revision="5a38c5eda9989b72fe76cebf884da2e4acdb6971",
            is_experimental=True,
            validation_notice=validation_notice,
            disease_context_notice=disease_notice,
            inputs_used=inference_out["inputs_evaluated"],
            nutrient_requirements=nutrient_reqs,
            commercial_recommendations=commercial,
            matching_local_stores=stores[:4],  # Top 4 matching retailers
            amazon_discovery=amazon_links,
            warnings=warnings,
        )


fertilizer_service = FertilizerAdvisoryService()

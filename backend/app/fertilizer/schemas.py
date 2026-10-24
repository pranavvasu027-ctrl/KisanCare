"""
Pydantic schemas for KisanCare Real ML Fertilizer Advisory & Store Discovery.
"""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field


class FertilizerInput(BaseModel):
    """Farmer and soil input payload for fertilizer advisory."""
    crop_name: str = Field(..., min_length=1, max_length=100, description="Host crop name.")
    target_yield: float = Field(default=3500.0, gt=0, description="Target yield in kg/ha.")
    field_size: float = Field(default=1.0, gt=0, description="Cultivated field area in hectares.")
    ph: float = Field(..., ge=3.0, le=11.0, description="Soil pH (water).")
    organic_carbon: float = Field(..., ge=0.0, le=100.0, description="Soil Organic Carbon (g/kg or %).")
    total_nitrogen: float = Field(..., ge=0.0, description="Total Soil Nitrogen (g/kg or kg/ha).")
    available_phosphorus: float = Field(..., ge=0.0, description="Available Phosphorus (M3 / Bray / Olsen mg/kg).")
    exchangeable_potassium: float = Field(..., ge=0.0, description="Exchangeable Potassium (mmol+/kg or mg/kg).")
    soil_moisture: Optional[float] = Field(default=20.0, ge=0.0, le=100.0, description="Soil moisture percentage.")
    locality: Optional[str] = Field(default=None, max_length=200, description="Village or locality name.")
    pin_code: Optional[str] = Field(default=None, max_length=10, description="Postal PIN code.")
    district: Optional[str] = Field(default="Akola", max_length=100, description="Agricultural district.")
    disease_context: Optional[str] = Field(default=None, description="Optional diagnostic context from preceding disease scan.")

    model_config = ConfigDict(arbitrary_types_allowed=True)


class NutrientRequirement(BaseModel):
    """Predicted nutrient requirement with units and timing."""
    nutrient: str = Field(..., description="Nutrient or amendment name (e.g. Nitrogen, P2O5, K2O, Lime).")
    quantity: float = Field(..., description="Recommended quantity.")
    unit: str = Field(default="kg/ha", description="Measurement unit.")
    application_stage: Optional[str] = Field(None, description="Recommended phenological application timing.")
    description: str = Field(..., description="Nutritional agronomic rationale.")


class FertilizerStoreProduct(BaseModel):
    """Catalog product item in local fertilizer store."""
    product_name: str = Field(..., description="Commercial fertilizer product name.")
    nutrient_grade: str = Field(..., description="NPK grade or chemical composition.")
    mock_price_inr: float = Field(..., description="Simulated retail price in INR.")
    unit: str = Field(default="50 kg bag", description="Packaging unit.")
    mock_stock_bags: int = Field(..., description="Simulated in-stock quantity.")
    in_stock: bool = Field(True, description="Stock availability status.")


class FertilizerStore(BaseModel):
    """Local fertilizer retailer demo listing."""
    store_id: str = Field(..., description="Unique retailer identifier.")
    store_name: str = Field(..., description="Store or Krishi Kendra name.")
    address: str = Field(..., description="Street address / landmark.")
    village: str = Field(..., description="Village or locality.")
    district: str = Field(..., description="District.")
    pin_code: str = Field(..., description="Postal PIN code.")
    contact_phone: str = Field(..., description="Simulated contact number.")
    distance_km: Optional[float] = Field(None, description="Calculated distance in km if coordinates exist.")
    locality_match_level: str = Field("same_district", description="same_village | same_pincode | same_district | regional_demo")
    is_demo_inventory: bool = Field(True, description="Strict demo inventory indicator.")
    available_products: List[FertilizerStoreProduct] = Field(default_factory=list)
    disclaimer: str = Field(
        default="Demo inventory — verify with the retailer before visiting.",
        description="Farmer advisory disclaimer."
    )


class AmazonProductLink(BaseModel):
    """Verified Amazon.in product search query link with disclosure."""
    product_name: str = Field(..., description="Fertilizer formulation name.")
    search_query: str = Field(..., description="Exact search keywords.")
    amazon_search_url: str = Field(..., description="Direct Amazon.in search URL.")
    attribution: str = Field(default="Amazon.in verified product search link")
    disclaimer: str = Field(
        default="Prices and stock vary on Amazon.in. Verify seller rating and delivery time before ordering."
    )


class CommercialFertilizerRecommendation(BaseModel):
    """Formulation-based commercial fertilizer dose calculated from nutrient needs."""
    fertilizer_name: str = Field(..., description="E.g. Urea, DAP, MOP, SSP.")
    grade: str = Field(..., description="Grade e.g. 46-0-0.")
    dose_kg_ha: float = Field(..., description="Calculated commercial dose in kg/ha.")
    bags_50kg_per_ha: float = Field(..., description="Calculated number of 50kg bags per hectare.")
    application_timing: str = Field(..., description="Basal or top-dressing split.")


class FertilizerAdvisoryResponse(BaseModel):
    """Complete typed response for Fertilizer & Soil Nutrient Advisory."""
    status: str = Field("success", description="success | unvalidated_crop | missing_soil_inputs | model_unavailable")
    crop: str = Field(..., description="Target crop.")
    field_size_ha: float = Field(..., description="Field size evaluated.")
    target_yield_kg_ha: float = Field(..., description="Target yield evaluated.")
    model_identifier: str = Field("DNgigi/FertiliserApplication", description="ML model identifier.")
    model_revision: str = Field("5a38c5eda9989b72fe76cebf884da2e4acdb6971", description="Pinned HuggingFace commit SHA.")
    is_experimental: bool = Field(True, description="Experimental / unvalidated regional status.")
    validation_notice: str = Field(..., description="Regional and calibration limitations notice.")
    disease_context_notice: Optional[str] = Field(None, description="Clear segregation from disease diagnosis.")
    inputs_used: Dict[str, Any] = Field(default_factory=dict, description="Validated soil and farm inputs used.")
    nutrient_requirements: List[NutrientRequirement] = Field(default_factory=list, description="Raw ML-predicted nutrient needs.")
    commercial_recommendations: List[CommercialFertilizerRecommendation] = Field(default_factory=list, description="Calculated commercial fertilizers.")
    matching_local_stores: List[FertilizerStore] = Field(default_factory=list, description="Local demo fertilizer store discovery.")
    amazon_discovery: List[AmazonProductLink] = Field(default_factory=list, description="Amazon.in product search links.")
    warnings: List[str] = Field(default_factory=list, description="Operational, unit, and agronomic warnings.")

    model_config = ConfigDict(arbitrary_types_allowed=True)

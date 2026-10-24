"""Diagnostic inference route protected by API Key.

Strictly supports Cotton (DenseNet-121) and Soybean (ConvNeXt-Small).
All other crops are explicitly rejected with HTTP 422 Unprocessable Entity.
Provides simplified, safe farmer guidance payload.
"""

import io
from typing import List, Optional
from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from PIL import Image

from disease_pest_ai.api.auth import verify_api_key
from disease_pest_ai.inference.pipeline import DiseasePestPipeline

router = APIRouter(prefix="/api/v1", tags=["Diagnosis"])

SUPPORTED_CROPS = {"Cotton", "Soybean"}

VERIFIED_CLASSES = {
    "Cotton": {
        "Bacterial Blight",
        "Cotton Leaf Curl Virus",
        "Fusarium Wilt",
        "Healthy Foliage",
    },
    "Soybean": {
        "Downy Mildew",
        "Frogeye Leaf Spot",
        "Healthy Foliage",
        "Soybean Mosaic Virus",
        "Asian Soybean Rust",
        "Brown Spot (Septoria)",
    },
}

# Global pipeline instance initialized during app lifespan
_pipeline_instance: Optional[DiseasePestPipeline] = None


def set_pipeline(pipeline: DiseasePestPipeline):
    """Sets the singleton pipeline instance."""
    global _pipeline_instance
    _pipeline_instance = pipeline


def get_pipeline() -> DiseasePestPipeline:
    """Retrieves the preloaded pipeline instance."""
    global _pipeline_instance
    if _pipeline_instance is None:
        _pipeline_instance = DiseasePestPipeline(
            primary_disease_model="specialist",
            primary_pest_model="yolo_pest",
            lazy_load=False,
        )
    return _pipeline_instance


@router.post(
    "/diagnose",
    summary="Diagnose Plant Disease & Pests (API Key Protected)",
    description="Uploads a plant image and agronomic contract fields to perform neural disease diagnosis "
                "(strictly Cotton or Soybean), pest localization, crop match validation, and CIB&RC treatment retrieval.",
)
async def diagnose_plant(
    file: UploadFile = File(..., description="Plant leaf image (JPEG/PNG/WEBP)"),
    crop_name: str = Form(..., description="Crop host name ('Cotton' or 'Soybean')"),
    location_state: str = Form("Maharashtra", description="State of cultivation in India"),
    growth_stage: str = Form("vegetative", description="Phenological growth stage"),
    image_type: str = Form("leaf", description="Image modality: 'leaf'"),
    generate_visual_explanation: bool = Form(False, description="Whether to generate Grad-CAM heatmap"),
    _api_key: str = Depends(verify_api_key),
):
    """Diagnoses disease from image with statutory treatment recommendations."""
    # 1. Enforce strict crop restriction
    clean_crop = crop_name.strip().title()
    if clean_crop not in SUPPORTED_CROPS:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Crop '{crop_name}' is not supported. KisanCare Disease Detection only supports 'Cotton' and 'Soybean'.",
        )

    # 2. Read file bytes
    try:
        contents = await file.read()
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to read uploaded image file: {e}",
        )

    if not contents:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Uploaded file is empty.",
        )

    # 3. Validate PIL image
    try:
        pil_img = Image.open(io.BytesIO(contents))
        pil_img.verify()
        pil_img = Image.open(io.BytesIO(contents))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Invalid or corrupted image format: {e}",
        )

    if pil_img.width < 128 or pil_img.height < 128:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Image resolution ({pil_img.width}x{pil_img.height}) is too small. Minimum required is 128x128 pixels.",
        )

    if pil_img.mode != "RGB":
        pil_img = pil_img.convert("RGB")

    # 4. Execute inference pipeline
    pipeline = get_pipeline()
    try:
        result = pipeline.predict(
            plant_image=pil_img,
            crop_name=clean_crop,
            location_state=location_state.strip(),
            growth_stage=growth_stage.strip(),
            image_type=image_type.strip(),
            generate_visual_explanation=generate_visual_explanation,
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Inference execution failed: {e}",
        )

    return result.model_dump()


@router.get(
    "/specialists",
    summary="List Registered Crop Specialists",
    description="Returns registry status for Cotton and Soybean specialists.",
)
async def list_specialists():
    from disease_pest_ai.specialists.registry import specialist_registry
    return specialist_registry.get_registry_status()


@router.post(
    "/disease-detection",
    summary="Farmer Disease Detection Endpoint",
    description="Accepts crop selection ('Cotton' or 'Soybean') and leaf photo, returning direct diagnosis.",
)
async def detect_disease_frontend_compat(
    file: Optional[UploadFile] = File(None),
    crop: Optional[str] = Form(None),
    crop_name: Optional[str] = Form(None),
    location_state: Optional[str] = Form("Maharashtra"),
    growth_stage: Optional[str] = Form("vegetative"),
    image_type: Optional[str] = Form("leaf"),
    symptoms: Optional[str] = Form(None),
    sample_id: Optional[str] = Form(None),
    generate_visual_explanation: bool = Form(False),
):
    resolved_crop = crop or crop_name or ""
    clean_crop = resolved_crop.strip().title()

    # 1. Validate crop selection
    if clean_crop not in SUPPORTED_CROPS:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Crop '{resolved_crop}' is not supported. KisanCare Disease Detection only supports 'Cotton' and 'Soybean'.",
        )

    # 2. Validate file upload presence (strictly require leaf image)
    if not file or not file.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Leaf photo is required. Please upload a clear photo of the leaf.",
        )

    contents = await file.read()
    if not contents:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Uploaded file is empty.",
        )

    try:
        pil_img = Image.open(io.BytesIO(contents))
        pil_img.verify()
        pil_img = Image.open(io.BytesIO(contents))
        if pil_img.mode != "RGB":
            pil_img = pil_img.convert("RGB")
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Invalid image format: {e}",
        )

    if pil_img.width < 128 or pil_img.height < 128:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Image resolution ({pil_img.width}x{pil_img.height}) is too small. Minimum required is 128x128 pixels.",
        )

    pipeline = get_pipeline()
    result = pipeline.predict(
        plant_image=pil_img,
        crop_name=clean_crop,
        location_state=location_state.strip(),
        growth_stage=growth_stage.strip(),
        image_type=image_type.strip(),
        generate_visual_explanation=generate_visual_explanation,
    )
    data = result.model_dump()

    # Determine farmer status, confidence, and recommended next steps
    routing_info = result.provenance.context.get("specialist_routing", {})
    verified_set = VERIFIED_CLASSES.get(clean_crop, set())
    is_valid_condition = result.disease.condition in verified_set

    is_abstaining = (
        routing_info.get("abstention", False)
        or result.disease.status in ("low_score", "unsupported_crop", "insufficient_evidence")
        or result.disease.score < 0.40
        or not is_valid_condition
    )
    is_healthy = is_valid_condition and (result.disease.condition_type.value == "healthy" or "healthy" in result.disease.condition.lower())
    confidence_int = int(round(result.disease.score * 100))

    recommended_steps: List[str] = []
    if is_abstaining:
        farmer_status = "unable_to_determine"
        status_label = "Unable to Determine Reliably"
        display_disease = "Unable to identify the disease reliably. Please upload a clearer leaf photo."
        confidence_display = "Confidence too low for safe identification"
        recommended_steps = [
            "Take a close-up photo in good natural daylight, focusing on the leaf lesion or discolored area.",
            "Avoid blurry photos, distant foliage, or strong shadow/glare in the frame.",
            "Strictly avoid applying chemical pesticides or fungicides without a verified diagnosis.",
            "If symptoms are spreading, take a fresh leaf sample to your nearest Krishi Vigyan Kendra (KVK) or State Agricultural Extension Officer.",
        ]
    elif is_healthy:
        farmer_status = "healthy"
        status_label = "Healthy Leaf"
        display_disease = "Healthy Foliage"
        confidence_display = f"{confidence_int}% (Model confidence score)"
        recommended_steps = [
            f"Your {clean_crop} foliage looks healthy with no visible signs of active foliar infection.",
            "No chemical pesticide or fungicide treatment is required.",
            "Maintain regular weekly crop scouting and balanced nutrient/water management.",
        ]
    else:
        farmer_status = "disease_detected"
        status_label = "Likely Disease Detected"
        display_disease = result.disease.condition
        confidence_display = f"{confidence_int}% (Model confidence score)"

        if clean_crop == "Cotton":
            if "bacterial blight" in result.disease.condition.lower():
                recommended_steps = [
                    "Field sanitation: Remove and safely dispose of heavily blighted leaves to prevent bacterial spread.",
                    "Avoid working in or irrigating fields when foliage is wet, as water splash spreads bacteria.",
                    "If confirmed by local agronomist: Copper Oxychloride 50% WP @ 2.5–3.0 kg/ha may be applied.",
                    "Consult your local Krishi Vigyan Kendra (KVK) officer before applying any chemical spray.",
                ]
            elif "curl virus" in result.disease.condition.lower():
                recommended_steps = [
                    "CLCuV is viral — do NOT apply chemical fungicides (fungicides cannot cure viral diseases).",
                    "Vector management: Install yellow sticky traps (15–20/ha) to monitor and suppress whitefly vectors.",
                    "Rogue out and bury severely infected plants in early growth stages to minimize virus reservoir.",
                    "Consult your local agricultural extension officer for regional whitefly IPM guidance.",
                ]
            elif "fusarium" in result.disease.condition.lower():
                recommended_steps = [
                    "Soil management: Fusarium is soil-borne; practice crop rotation with non-host cereals to break the cycle.",
                    "Improve field drainage to prevent water stagnation around plant root zones.",
                    "Bio-control: Apply Trichoderma viride enriched farmyard manure around root zones.",
                    "Seek expert confirmation from an agronomist before attempting chemical soil drenching.",
                ]
            else:
                recommended_steps = [
                    f"Isolate symptomatic {clean_crop} plants and monitor field progression.",
                    "Consult local extension officer or KVK agronomist with a physical leaf sample.",
                ]
        elif clean_crop == "Soybean":
            if "frogeye" in result.disease.condition.lower():
                recommended_steps = [
                    "Canopy aeration: Ensure adequate spacing so leaves dry quickly after morning dew or rain.",
                    "Rotate with non-host crops like corn or sorghum to reduce fungal inoculum in the field.",
                    "If disease pressure exceeds economic threshold and is verified by agronomist: Pyraclostrobin 20% WG may be used.",
                    "Check with local KVK before chemical spraying.",
                ]
            elif "rust" in result.disease.condition.lower():
                recommended_steps = [
                    "Early action: Asian rust spreads fast in humid weather; inspect lower leaf surfaces weekly.",
                    "Avoid late-evening overhead sprinkler irrigation that keeps leaves wet overnight.",
                    "If verified in your area, contact agricultural officer immediately for approved protective fungicide advisory (e.g. Hexaconazole 5% EC).",
                ]
            elif "downy mildew" in result.disease.condition.lower():
                recommended_steps = [
                    "Sanitation: Deep plow crop residues after harvest to bury overwintering fungal spores.",
                    "Improve field drainage in low-lying spots to prevent standing water.",
                    "Consult local agricultural officer for threshold-based copper or bio-fungicide advice.",
                ]
            elif "mosaic virus" in result.disease.condition.lower():
                recommended_steps = [
                    "Viral condition: Do NOT apply chemical fungicides (fungicides cannot cure plant viruses).",
                    "Rogue out infected plants showing mosaic mottle early to protect surrounding crop.",
                    "Monitor aphid vectors and spray botanical Neem Seed Kernel Extract (NSKE 5%) if needed.",
                    "Use certified virus-free seeds for next planting season.",
                ]
            elif "septoria" in result.disease.condition.lower() or "brown spot" in result.disease.condition.lower():
                recommended_steps = [
                    "Field sanitation: Avoid cultivating fields when foliage is wet.",
                    "Rotate crops with corn or sorghum to interrupt the fungal life cycle.",
                    "Consult local extension officer if lower-leaf spotting progresses up into middle canopy.",
                ]
            else:
                recommended_steps = [
                    f"Isolate symptomatic {clean_crop} foliage and practice clean weeding.",
                    "Consult local KVK or extension officer with a physical sample.",
                ]

    data["farmer_guidance"] = {
        "status": farmer_status,
        "status_label": status_label,
        "disease_name": display_disease,
        "confidence_percent": confidence_int if not is_abstaining else None,
        "confidence_display": confidence_display,
        "recommended_steps": recommended_steps,
        "crop": clean_crop,
        "is_healthy": is_healthy,
        "is_abstaining": is_abstaining,
    }

    # Backward compatibility fields
    data["condition"] = display_disease
    data["scientific_name"] = result.disease.condition
    data["confidence_percent"] = confidence_int if not is_abstaining else 0
    data["treatments"] = {"chemical": []}
    if not is_healthy and not is_abstaining and result.treatment and result.treatment.disease_recommendations:
        chem_list = []
        for c in result.treatment.disease_recommendations.chemical_candidates:
            chem_list.append({
                "chemical_name": getattr(c, "active_ingredient", getattr(c, "chemical_name", "Chemical")),
                "dosage": getattr(c, "dose_information", getattr(c, "formulation", "As per label")),
                "cpr_registration": getattr(c, "source_id", getattr(c, "cibrc_registration_number", "CIBRC Registered")),
                "waiting_period_days": getattr(c, "waiting_period_days", None),
            })
        data["treatments"]["chemical"] = chem_list

    data["fusion_outcome"] = routing_info.get("fusion_outcome", "single_model")
    data["model_identifier"] = routing_info.get("model_attribution", result.provenance.disease_model)
    data["abstention"] = is_abstaining
    data["abstention_reason"] = routing_info.get("abstention_reason")
    return {
        "status": "success",
        "data": data,
        "farmer_guidance": data["farmer_guidance"],
        "condition": data["condition"],
        "confidence_percent": data["confidence_percent"],
        "isDemo": False,
    }

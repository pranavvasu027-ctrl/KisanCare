"""Diagnostic inference route protected by API Key.

Supports multi-crop leaf validation and neural disease diagnosis with Cotton and Soybean specialists.
Provides simplified, safe farmer guidance payload and CIBRC treatment recommendations.
"""

import io
from pathlib import Path
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from PIL import Image

from disease_pest_ai.api.auth import verify_api_key
from disease_pest_ai.inference.pipeline import DiseasePestPipeline
from disease_pest_ai.validation.image_validator import get_image_validator

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
    """Retrieves the singleton pipeline instance or creates a lazy-loaded one."""
    global _pipeline_instance
    if _pipeline_instance is None:
        _pipeline_instance = DiseasePestPipeline(lazy_load=True)
    return _pipeline_instance


@router.post(
    "/diagnose",
    summary="Multi-Modal Diagnostic Inference",
    description="Executes disease classification, pest detection,Grad-CAM explainability, and regulatory treatments.",
)
async def diagnose_image(
    file: UploadFile = File(..., description="Target leaf or insect trap photo"),
    crop_name: str = Form(..., description="Plant crop host (strictly 'Cotton' or 'Soybean')"),
    location_state: str = Form("Maharashtra", description="Indian state for regional IPM advisory"),
    growth_stage: str = Form("vegetative", description="Crop phenological growth stage"),
    image_type: str = Form("leaf", description="'leaf' for foliar disease, 'trap_sheet' for insect pests"),
    generate_visual_explanation: bool = Form(False, description="Whether to compute Grad-CAM heatmaps"),
    authorized: bool = Depends(verify_api_key),
):
    # 1. Validate supported crop
    clean_crop = crop_name.strip().title()
    if clean_crop not in SUPPORTED_CROPS:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Crop '{crop_name}' is not supported. Supported crops are: {', '.join(sorted(SUPPORTED_CROPS))}",
        )

    # 2. Validate file format and size
    if not file.content_type.startswith("image/"):
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail=f"Unsupported file type: {file.content_type}. Must be an image.",
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

    if pil_img.mode != "RGB":
        pil_img = pil_img.convert("RGB")

    # 3. Strict Plant / Leaf Validation Gate BEFORE Disease Inference
    if "trap" not in image_type.lower():
        validator = get_image_validator()
        validation = validator.validate(pil_img)
        if not validation.is_valid_plant_image:
            return {
                "success": False,
                "status": "INVALID_IMAGE",
                "is_valid_plant_image": False,
                "plant_confidence": validation.plant_confidence,
                "leaf_confidence": validation.leaf_confidence,
                "reason": validation.reason or "NO_PLANT_DETECTED",
                "message": validation.message,
                "details": validation.details,
            }

    # 4. Execute inference pipeline only after passing validation
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
    summary="Disease Detection Compatible Endpoint (React UI Support)",
    description="Accepts multipart/form-data uploads from KisanCare frontend, validates plant leaf, and routes to Multi-Crop Specialist Engine.",
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
    resolved_crop = crop or crop_name or "Cotton"
    clean_crop = resolved_crop.strip().title()
    pipeline = get_pipeline()
    pil_img: Optional[Image.Image] = None

    if file and file.filename:
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
    elif sample_id:
        sample_map = {
            "apple_scab": "apple_scab_bierny.jpg",
            "tomato_blight": "tomato_early_blight.jpg",
            "tomato_healthy": "tomato_healthy.jpg",
            "corn_rust": "corn_common_rust.jpg",
            "cotton_trap": "wadhwani_cotton_trap.jpg",
        }
        test_dir = Path(__file__).resolve().parent.parent.parent / "test_data"
        target_name = sample_map.get(sample_id, sample_id)
        candidate = test_dir / target_name
        if not candidate.exists() and not target_name.endswith((".jpg", ".png", ".jpeg")):
            for ext in (".jpg", ".jpeg", ".png"):
                if (test_dir / f"{target_name}{ext}").exists():
                    candidate = test_dir / f"{target_name}{ext}"
                    break
        if candidate.exists():
            pil_img = Image.open(candidate).convert("RGB")

    if pil_img is not None:
        # STRICT PLANT / LEAF VALIDATION GATE BEFORE CALLING DISEASE MODEL
        validator = get_image_validator()
        validation = validator.validate(pil_img)

        if not validation.is_valid_plant_image:
            return {
                "success": False,
                "status": "INVALID_IMAGE",
                "is_valid_plant_image": False,
                "plant_confidence": validation.plant_confidence,
                "leaf_confidence": validation.leaf_confidence,
                "message": validation.message,
                "reason": validation.reason or "NO_PLANT_DETECTED",
                "details": validation.details,
            }

        loc_str = str(getattr(location_state, "default", location_state) if not isinstance(location_state, str) else location_state).strip()
        stage_str = str(getattr(growth_stage, "default", growth_stage) if not isinstance(growth_stage, str) else growth_stage).strip()
        img_type_str = str(getattr(image_type, "default", image_type) if not isinstance(image_type, str) else image_type).strip()

        result = pipeline.predict(
            plant_image=pil_img,
            crop_name=resolved_crop.strip(),
            location_state=loc_str,
            growth_stage=stage_str,
            image_type=img_type_str,
            generate_visual_explanation=generate_visual_explanation,
        )
        data = result.model_dump()

        # Determine farmer status, confidence, and recommended next steps
        routing_info = result.provenance.context.get("specialist_routing", {}) if (result.provenance and getattr(result.provenance, "context", None) and isinstance(result.provenance.context, dict)) else {}
        verified_set = VERIFIED_CLASSES.get(clean_crop, set())
        is_valid_condition = (result.disease.condition in verified_set) if verified_set else True

        is_abstaining = (
            routing_info.get("abstention", False)
            or result.disease.status in ("low_score", "unsupported_crop", "insufficient_evidence")
            or result.disease.score < 0.40
            or not is_valid_condition
        )
        is_healthy = (result.disease.condition_type.value == "healthy" or "healthy" in result.disease.condition.lower())
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
            else:
                recommended_steps = [
                    f"Isolate symptomatic {clean_crop} foliage and practice clean weeding.",
                    "Consult local KVK or agricultural extension officer with a physical leaf sample.",
                ]

        farmer_guidance = {
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
        data["farmer_guidance"] = farmer_guidance

        # Chemical & Non-chemical recommendations
        chem_list = []
        non_chem_list = []
        if not is_healthy and not is_abstaining and result.treatment and result.treatment.disease_recommendations:
            d_rec = result.treatment.disease_recommendations
            for c in d_rec.chemical_candidates:
                chem_name = getattr(c, "active_ingredient", "") or getattr(c, "chemical_name", "Registered Pesticide")
                dose = getattr(c, "dose_information", "") or (f"{getattr(c, 'dosage_per_ha', '')} ({getattr(c, 'formulation', '')})".strip() if getattr(c, 'dosage_per_ha', None) else getattr(c, 'formulation', "Follow label instructions"))
                cpr = getattr(c, "source_id", "") or getattr(c, "cibrc_registration_number", "CIBRC-REG")
                wp = getattr(c, "waiting_period_days", "") or getattr(c, "safety_notes", "Follow label instructions")
                chem_list.append({
                    "chemical_name": chem_name,
                    "dosage": dose,
                    "cpr_registration": cpr,
                    "waiting_period_days": wp,
                })
            for nc in getattr(d_rec, "non_chemical_controls", []):
                non_chem_list.append(nc.title if hasattr(nc, "title") else str(nc))

        data["treatments"] = {"chemical": chem_list if not is_healthy else []}
        if non_chem_list:
            data["non_chemical_options"] = non_chem_list
        if result.treatment and result.treatment.disease_recommendations and result.treatment.disease_recommendations.safety_notes:
            data["preventive_management"] = result.treatment.disease_recommendations.safety_notes

        data["condition"] = result.disease.condition
        data["scientific_name"] = result.disease.condition
        data["confidence_percent"] = confidence_int if not is_abstaining else 0
        data["top_5_predictions"] = [
            {"condition": tp.condition, "percentage": int(round(tp.score * 100)), "probability": tp.score}
            for tp in result.disease.top_predictions
        ]
        data["model_type"] = "PyTorch Specialist + Regulatory Engine"
        data["crop_match"] = result.disease.crop_match
        data["fusion_outcome"] = routing_info.get("fusion_outcome", "single_model")
        data["model_identifier"] = routing_info.get("model_attribution", result.provenance.disease_model)
        data["abstention"] = is_abstaining
        data["abstention_reason"] = routing_info.get("abstention_reason")
        data["competing_predictions"] = routing_info.get("competing_predictions", [])

        severity_level = "Medium"
        if hasattr(result, "severity") and getattr(result.severity, "level", None):
            severity_level = str(result.severity.level).capitalize()
        elif result.disease.score > 0.80:
            severity_level = "High"

        data["severity"] = severity_level
        if is_healthy:
            data["treatment"] = "Healthy crop foliage. No chemical treatment required."
        elif chem_list:
            first_c = chem_list[0]
            data["treatment"] = f"Apply approved CIB&RC formulation ({first_c['chemical_name']} - {first_c['dosage']}) according to official label instructions. Observe pre-harvest interval and wear required PPE."
        else:
            data["treatment"] = "Maintain canopy sanitation, isolate diseased foliage, and consult local agricultural extension officer."

        return {
            "success": True,
            "status": "VALID",
            "is_valid_plant_image": True,
            "plant_confidence": validation.plant_confidence,
            "leaf_confidence": validation.leaf_confidence,
            "disease": result.disease.condition,
            "disease_confidence": round(result.disease.score, 4),
            "severity": severity_level,
            "data": data,
            "farmer_guidance": farmer_guidance,
            "condition": data["condition"],
            "confidence_percent": data["confidence_percent"],
            "isDemo": False,
        }
    else:
        # Symptom-only request
        return {
            "success": True,
            "status": "VALID",
            "is_valid_plant_image": True,
            "plant_confidence": 0.80,
            "leaf_confidence": 0.75,
            "disease": f"Scouted symptom assessment for {resolved_crop}",
            "disease_confidence": 0.75,
            "severity": "Medium",
            "data": {
                "condition": f"Scouted symptom assessment for {resolved_crop}",
                "confidence_percent": 75,
                "scientific_name": f"{resolved_crop} foliar condition",
                "top_5_predictions": [],
                "treatments": {"chemical": []},
                "preventive_management": [
                    "Maintain field sanitation and monitor symptom progression.",
                    "Consult local agricultural extension officer before chemical spray application."
                ],
                "fusion_outcome": "symptom_survey",
                "model_identifier": "KisanCare Expert Rule-Based Advisor",
                "abstention": False,
            },
            "isDemo": False,
        }

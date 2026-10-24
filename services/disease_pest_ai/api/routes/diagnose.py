"""Diagnostic inference route protected by API Key."""

import io
from typing import Optional
from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from PIL import Image

from disease_pest_ai.api.auth import verify_api_key
from disease_pest_ai.inference.pipeline import DiseasePestPipeline

router = APIRouter(prefix="/api/v1", tags=["Diagnosis"])

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
            primary_disease_model="efficientnet",
            primary_pest_model="yolo_pest",
            lazy_load=False,
        )
    return _pipeline_instance


@router.post(
    "/diagnose",
    summary="Diagnose Plant Disease & Pests (API Key Protected)",
    description="Uploads a plant image and agronomic contract fields to perform neural disease diagnosis, "
                "pest localization, crop match validation, and CIB&RC treatment retrieval.",
)
async def diagnose_plant(
    file: UploadFile = File(..., description="Plant leaf, whole crop, or sticky trap image (JPEG/PNG/WEBP)"),
    crop_name: str = Form(..., description="Crop host name (e.g. Tomato, Apple, Corn, Potato, Cotton)"),
    location_state: str = Form(..., description="State of cultivation in India (e.g. Maharashtra, Punjab)"),
    growth_stage: str = Form(..., description="Phenological growth stage (e.g. seedling, vegetative, flowering, fruiting)"),
    image_type: str = Form("leaf", description="Image modality: 'leaf', 'field_crop', 'fruit', 'stem', 'whole_plant', 'trap_sticky_sheet'"),
    generate_visual_explanation: bool = Form(True, description="Whether to generate Grad-CAM heatmap and box overlays"),
    _api_key: str = Depends(verify_api_key),
):
    """Diagnoses disease and pest from image with statutory treatment recommendations."""
    # 1. Read file bytes
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

    # 2. Validate PIL image
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

    # 3. Execute inference pipeline
    pipeline = get_pipeline()
    try:
        result = pipeline.predict(
            plant_image=pil_img,
            crop_name=crop_name.strip(),
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

    # Return Pydantic dictionary
    return result.model_dump()

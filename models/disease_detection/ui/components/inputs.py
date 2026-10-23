"""
Validated UI Inputs Component (Sections 3, 4, 5, 6, 18).
"""

import io
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

from PIL import Image
import streamlit as st

TEST_DATA_DIR = Path(__file__).resolve().parent.parent.parent / "test_data"

SUPPORTED_CROPS = [
    "Tomato",
    "Apple",
    "Corn",
    "Potato",
    "Bell Pepper",
    "Cotton",
    "Grape",
    "Orange",
    "Peach",
    "Cherry",
    "Squash",
    "Strawberry",
    "Other / Unsupported Crop",
]

INDIAN_STATES = [
    "Andhra Pradesh",
    "Assam",
    "Bihar",
    "Chhattisgarh",
    "Gujarat",
    "Haryana",
    "Himachal Pradesh",
    "Jammu and Kashmir",
    "Jharkhand",
    "Karnataka",
    "Kerala",
    "Madhya Pradesh",
    "Maharashtra",
    "Odisha",
    "Punjab",
    "Rajasthan",
    "Tamil Nadu",
    "Telangana",
    "Uttar Pradesh",
    "Uttarakhand",
    "West Bengal",
]

IMAGE_TYPES = [
    "leaf",
    "field_crop",
    "fruit",
    "stem",
    "whole_plant",
    "trap_sticky_sheet",
]

SAMPLE_IMAGES = {
    "Select an example test image...": None,
    "Tomato Early Blight (Foliar Field Sample)": ("tomato_early_blight.jpg", "Tomato", "Maharashtra", "fruiting", "leaf"),
    "Tomato Healthy (Lab Control Leaf)": ("tomato_healthy.jpg", "Tomato", "Karnataka", "vegetative", "leaf"),
    "Apple Scab (BiernyVR Test Foliar)": ("apple_scab_bierny.jpg", "Apple", "Himachal Pradesh", "fruiting", "leaf"),
    "Corn Common Rust (Field Macro)": ("corn_common_rust.jpg", "Corn", "Bihar", "vegetative", "leaf"),
    "Cotton Pheromone Trap Sheet (Wadhwani BOLLWM)": ("wadhwani_cotton_trap.jpg", "Cotton", "Punjab", "boll_formation", "trap_sticky_sheet"),
}

CROP_STAGE_MAP = {
    "Cotton": ["seedling", "vegetative", "squaring", "flowering", "boll_formation", "harvesting"],
    "Corn": ["seedling", "vegetative", "tasseling", "silking", "dough", "maturity"],
    "Tomato": ["seedling", "vegetative", "flowering", "fruiting", "harvesting"],
    "Potato": ["sprouting", "vegetative", "tuber_initiation", "tuber_bulking", "maturity"],
    "Apple": ["dormant", "bud_break", "bloom", "fruit_set", "fruiting", "harvest"],
}

DEFAULT_STAGES = ["seedling", "vegetative", "flowering", "fruiting", "maturity"]


def validate_uploaded_image(image_bytes: bytes, filename: str) -> Tuple[Optional[Image.Image], Optional[str]]:
    """
    Validates image according to Section 5 requirements:
    - format validity
    - readable stream
    - RGB conversion
    - minimum useful resolution (>= 128x128)
    """
    try:
        pil_img = Image.open(io.BytesIO(image_bytes))
        pil_img.verify()
        # Re-open after verify
        pil_img = Image.open(io.BytesIO(image_bytes))
    except Exception as e:
        return None, f"Corrupted or invalid image stream: {e}"

    # Format check
    fmt = (pil_img.format or "").upper()
    if fmt not in ("JPEG", "JPG", "PNG", "WEBP", "TIFF"):
        return None, f"Unsupported image format '{fmt}'. Please upload JPEG, PNG, or WEBP."

    # Resolution check
    w, h = pil_img.size
    if w < 128 or h < 128:
        return None, f"Image resolution ({w}x{h}) is too low. Minimum required size is 128x128 pixels."

    # Convert to RGB
    if pil_img.mode != "RGB":
        pil_img = pil_img.convert("RGB")

    return pil_img, None


def render_input_form() -> Optional[Dict[str, Any]]:
    """
    Renders the unified input section with crop-aware dynamics.
    Returns input dictionary if user triggers analysis, else None.
    """
    st.subheader("1. Plant Imagery & Agronomic Context")

    # Sample Preset Helper
    preset_choice = st.selectbox(
        "Load Pre-Configured Test Benchmark Sample (Optional):",
        options=list(SAMPLE_IMAGES.keys()),
        index=0,
    )

    preset_data = SAMPLE_IMAGES.get(preset_choice)

    col1, col2 = st.columns([1, 1], gap="medium")

    with col1:
        st.markdown("##### Upload Plant Image")
        uploaded_file = st.file_uploader(
            "Choose a leaf, whole-plant, or sticky trap image:",
            type=["jpg", "jpeg", "png", "webp"],
            help="Upload clear field, laboratory, or pheromone sticky trap imagery.",
        )

        selected_image: Optional[Image.Image] = None
        img_validation_error: Optional[str] = None
        img_display_name = ""

        if uploaded_file is not None:
            image_bytes = uploaded_file.read()
            selected_image, img_validation_error = validate_uploaded_image(image_bytes, uploaded_file.name)
            img_display_name = uploaded_file.name
        elif preset_data is not None:
            sample_filename, def_crop, def_state, def_stage, def_type = preset_data
            sample_path = TEST_DATA_DIR / sample_filename
            if sample_path.exists():
                with open(sample_path, "rb") as f:
                    selected_image, img_validation_error = validate_uploaded_image(f.read(), sample_filename)
                img_display_name = f"Sample: {sample_filename}"
            else:
                img_validation_error = f"Test sample not found: {sample_filename}"

        if img_validation_error:
            st.error(f"❌ Image Error: {img_validation_error}")
        elif selected_image is not None:
            st.image(selected_image, caption=f"Selected: {img_display_name} ({selected_image.width}x{selected_image.height})", use_container_width=True)

    with col2:
        st.markdown("##### Agronomic Metadata Contract")

        # Crop selection
        def_crop_idx = 0
        if preset_data:
            _, p_crop, _, _, _ = preset_data
            if p_crop in SUPPORTED_CROPS:
                def_crop_idx = SUPPORTED_CROPS.index(p_crop)

        selected_crop_item = st.selectbox(
            "Crop Name:",
            options=SUPPORTED_CROPS,
            index=def_crop_idx,
            help="Select the botanical crop host.",
        )

        is_unsupported = False
        if selected_crop_item == "Other / Unsupported Crop":
            custom_crop = st.text_input("Enter Crop Name (Unsupported):", value="Dragonfruit")
            crop_name = custom_crop.strip()
            is_unsupported = True
            st.warning("⚠️ **UNSUPPORTED CROP:** This crop is outside the verified CIB&RC registry. Safe manual review will be enforced.")
        else:
            crop_name = selected_crop_item

        # State selection
        def_state_idx = 0
        if preset_data:
            _, _, p_state, _, _ = preset_data
            if p_state in INDIAN_STATES:
                def_state_idx = INDIAN_STATES.index(p_state)

        location_state = st.selectbox(
            "Location / State (India):",
            options=INDIAN_STATES,
            index=def_state_idx,
            help="State of cultivation for CIB&RC geographic lookup.",
        )

        # Dynamic Growth Stage
        stage_options = CROP_STAGE_MAP.get(crop_name, DEFAULT_STAGES)
        def_stage_idx = 0
        if preset_data:
            _, _, _, p_stage, _ = preset_data
            if p_stage in stage_options:
                def_stage_idx = stage_options.index(p_stage)

        growth_stage = st.selectbox(
            "Phenological Growth Stage:",
            options=stage_options,
            index=def_stage_idx,
            help="Crop phenology stage for agronomic contextualization.",
        )

        # Image Type (Only validated backend modalities)
        def_type_idx = 0
        if preset_data:
            _, _, _, _, p_type = preset_data
            if p_type in IMAGE_TYPES:
                def_type_idx = IMAGE_TYPES.index(p_type)

        image_type = st.selectbox(
            "Image Capture Modality (image_type):",
            options=IMAGE_TYPES,
            index=def_type_idx,
            help="Modal routing: 'trap_sticky_sheet' bypasses foliar disease classifier to prevent cardboard false alarms.",
        )

        if image_type == "trap_sticky_sheet":
            st.info("ℹ️ **Modal Routing Notice:** Pheromone sticky trap sheets bypass foliar pathology classification.")

        # Run Button
        st.markdown("<br>", unsafe_allow_html=True)
        analyze_clicked = st.button("🔍 ANALYZE PLANT", type="primary", use_container_width=True)

    if analyze_clicked:
        if selected_image is None or img_validation_error:
            st.error("Please provide a valid, readable plant image before analyzing.")
            return None

        return {
            "image": selected_image,
            "crop_name": crop_name,
            "location_state": location_state,
            "growth_stage": growth_stage,
            "image_type": image_type,
            "is_unsupported": is_unsupported,
            "filename": img_display_name,
        }

    return None

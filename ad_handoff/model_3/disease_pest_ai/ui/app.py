"""
Main Streamlit Application for Agriculture AI Disease & Pest Detection (Phase 5).

Launch Command:
    streamlit run ui/app.py
"""

from pathlib import Path
import sys
import time

import streamlit as st

# Setup system path to ensure package resolution
APP_DIR = Path(__file__).resolve().parent
MODULE_DIR = APP_DIR.parent
PROJECT_ROOT = MODULE_DIR.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
if str(MODULE_DIR) not in sys.path:
    sys.path.insert(0, str(MODULE_DIR))

from disease_pest_ai.inference.pipeline import DiseasePestPipeline
from disease_pest_ai.ui.components.header import (
    render_header,
    render_persistent_safety_banner,
    render_pipeline_status,
)
from disease_pest_ai.ui.components.inputs import render_input_form
from disease_pest_ai.ui.components.provenance import (
    render_model_evaluation_section,
    render_provenance_and_audit,
)
from disease_pest_ai.ui.components.results import render_diagnostic_results
from disease_pest_ai.ui.components.treatment import (
    render_aggregated_warnings,
    render_treatment_recommendations,
)

# Page configuration
st.set_page_config(
    page_title="Agriculture AI — Disease & Pest Detection",
    page_icon="🌾",
    layout="wide",
    initial_sidebar_state="expanded",
)


@st.cache_resource(show_spinner="Initializing Agriculture AI Pipeline (Pretrained Models & Knowledge Base)...")
def get_pipeline() -> DiseasePestPipeline:
    """Loads and caches the unified pipeline instance with pretrained weights."""
    return DiseasePestPipeline(
        primary_disease_model="efficientnet",
        primary_pest_model="yolo_pest",
        lazy_load=False,
    )


def main():
    # 1. Header and System Status
    render_header()
    render_pipeline_status()
    render_persistent_safety_banner()

    # 2. Sidebar Navigation and Agronomic Context
    with st.sidebar:
        st.markdown("### 🌾 Agriculture AI Console")
        st.markdown(
            "Welcome to the **Disease & Pest AI Diagnostic Assistant**. "
            "Upload leaf, plant, or trap imagery to obtain instant machine diagnosis "
            "and statutory CIB&RC treatment advisories."
        )

        st.markdown("---")
        st.markdown("#### ⚙️ Diagnostic Engine Specs")
        st.markdown(
            "- **Disease:** EfficientNetV2-S (PlantVillage)\n"
            "- **Pest:** YOLO11s Object Detector (IP102)\n"
            "- **CIB&RC DB:** Version 1.0.0 (31/03/2024)\n"
            "- **Explainability:** Grad-CAM + Box Overlays\n"
            "- **Device:** CPU Inference"
        )

        st.markdown("---")
        render_model_evaluation_section()

        st.markdown("---")
        st.caption("Google DeepMind Advanced Agentic Coding Pair Programmer — Phase 5")

    # 3. Initialize Pipeline
    try:
        pipeline = get_pipeline()
    except Exception as e:
        st.error(f"❌ Failed to initialize pipeline models: {e}")
        st.stop()

    # Preset via URL query parameter for automated testing and screenshot verification
    query_preset = st.query_params.get("preset")
    if query_preset and "last_result" not in st.session_state:
        preset_map = {
            "tomato_eb": ("tomato_early_blight.jpg", "Tomato", "Maharashtra", "fruiting", "leaf"),
            "tomato_healthy": ("tomato_healthy.jpg", "Tomato", "Karnataka", "vegetative", "leaf"),
            "apple_scab": ("apple_scab_bierny.jpg", "Apple", "Himachal Pradesh", "fruiting", "leaf"),
            "corn_rust": ("corn_common_rust.jpg", "Corn", "Bihar", "vegetative", "leaf"),
            "trap_sheet": ("wadhwani_cotton_trap.jpg", "Cotton", "Punjab", "boll_formation", "trap_sticky_sheet"),
            "mismatch": ("tomato_early_blight.jpg", "Cotton", "Gujarat", "vegetative", "leaf"),
        }
        if query_preset in preset_map:
            p_file, p_crop, p_state, p_stage, p_type = preset_map[query_preset]
            from disease_pest_ai.ui.components.inputs import TEST_DATA_DIR
            p_path = TEST_DATA_DIR / p_file
            if p_path.exists():
                from PIL import Image
                p_img = Image.open(p_path).convert("RGB")
                st.session_state["last_image"] = p_img
                p_res = pipeline.predict(
                    plant_image=p_img,
                    crop_name=p_crop,
                    location_state=p_state,
                    growth_stage=p_stage,
                    image_type=p_type,
                    generate_visual_explanation=True,
                )
                st.session_state["last_result"] = p_res

    # 4. Input Section
    input_data = render_input_form()

    # 5. Execution Trigger
    if input_data:
        st.session_state["last_image"] = input_data["image"]
        with st.spinner("Analyzing plant imagery through neural vision, taxonomy verification, and statutory CIB&RC registers..."):
            t_start = time.perf_counter()
            try:
                result = pipeline.predict(
                    plant_image=input_data["image"],
                    crop_name=input_data["crop_name"],
                    location_state=input_data["location_state"],
                    growth_stage=input_data["growth_stage"],
                    image_type=input_data["image_type"],
                    generate_visual_explanation=True,
                )
                t_duration = (time.perf_counter() - t_start) * 1000
                st.session_state["last_result"] = result
                st.session_state["last_latency_ms"] = t_duration
            except Exception as e:
                st.error(f"❌ Inference execution failed: {e}")
                return

    # 6. Render Results if Available
    if "last_result" in st.session_state and "last_image" in st.session_state:
        result = st.session_state["last_result"]
        orig_img = st.session_state["last_image"]

        render_diagnostic_results(result, orig_img)
        render_treatment_recommendations(result)
        render_aggregated_warnings(result)
        render_provenance_and_audit(result)


if __name__ == "__main__":
    main()

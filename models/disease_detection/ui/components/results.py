"""
UI Results & Diagnostic Presentation Component (Sections 7, 8, 9, 10, 11, 13, 15, 18).
"""

import base64
import io
from typing import Any, Optional

from PIL import Image
import streamlit as st

from disease_pest_ai.schemas.final_output import AgricultureDiseaseResult
from disease_pest_ai.schemas.outputs import ConditionType


def render_diagnostic_results(result: AgricultureDiseaseResult, original_image: Image.Image):
    """
    Renders unified diagnostic findings per Sections 7, 8, 9, 10, 11, 13, 15, 18.
    """
    st.markdown("---")
    st.subheader("2. Diagnostic Analysis & Findings")

    # 1. Crop Match & Mismatch Validation Banner (Section 11)
    if not result.disease.crop_match:
        st.error(
            f"⚠️ **CROP MISMATCH DETECTED**\n\n"
            f"- **User-Specified Crop:** `{result.input.crop}`\n"
            f"- **Diagnosed Pathology Host:** Incompatible with specified crop (`{result.disease.condition}`)\n\n"
            f"**Safety Enforcement:** Diagnosis is NOT accepted for chemical recommendation. "
            f"Chemical candidates have been automatically blocked to prevent off-label crop damage."
        )
    else:
        st.success(f"✓ **Crop Validation Confirmed:** Diagnosed condition is biologically compatible with `{result.input.crop}`.")

    # 2. Main Two-Column Diagnosis Overview
    col_dis, col_pest = st.columns([1, 1], gap="medium")

    # ------------------ DISEASE SECTION ------------------
    with col_dis:
        st.markdown("#### 🔬 Foliar Disease Diagnosis")

        if result.disease.status == "bypassed":
            st.info("ℹ️ **Foliar Classifier Bypassed:** Selected image modality (`trap_sticky_sheet`) is not a leaf.")
        else:
            # Condition badge
            cond_type_val = result.disease.condition_type.value if hasattr(result.disease.condition_type, "value") else str(result.disease.condition_type)
            st.metric(
                label=f"Diagnosed Condition ({cond_type_val.upper()})",
                value=result.disease.condition,
                delta=f"Confidence: {result.disease.score * 100:.1f}%",
            )

            st.write(f"**Classification Status:** `{result.disease.status}`")
            st.write(f"**Target Pathology Host:** `{result.input.crop}`")

            # Top predictions breakdown
            if result.disease.top_predictions:
                with st.expander("Top-5 Ranked Predictions (Raw Softmax)"):
                    for idx, tp in enumerate(result.disease.top_predictions, start=1):
                        st.write(f"**{idx}. {tp.condition}** ({tp.crop}) — Score: `{tp.score:.4f}`")

            st.caption("ℹ️ *AI-assisted image classification; field performance may differ from benchmark performance.*")

    # ------------------ PEST SECTION ------------------
    with col_pest:
        st.markdown("#### 🐛 Arthropod Pest Detection")

        if result.pests.status == "no_pest_detected":
            st.info("🟢 **NO PEST DETECTED**")
            st.caption("*(Notice: The absence of visible insect pests does NOT inherently indicate the plant is disease-free or completely healthy.)*")
        elif result.pests.status == "bypassed":
            st.warning("Pest detection was bypassed for this execution.")
        elif result.pests.count > 0:
            st.metric(
                label="Detected Pests Count",
                value=result.pests.count,
                delta=f"Primary: {result.pests.detections[0].pest}",
            )
            for idx, p in enumerate(result.pests.detections, start=1):
                compat_str = "✓ Host Match" if p.crop_compatible else "⚠️ Crop Incompatible"
                st.write(f"**{idx}. {p.pest}** — Score: `{p.score:.3f}` [{compat_str}]")
                st.code(f"Box Coordinates: {p.bounding_box}", language="text")
        else:
            st.info("No pests localized passing detection threshold.")

    # ------------------ SEVERITY SECTION (Section 13 & 18) ------------------
    st.markdown("#### 📏 Visual Disease Severity")
    st.info(
        f"**Severity Status:** `{result.severity.status.upper()}`\n\n"
        f"Calibrated pixel-level foliar lesion segmentation is not integrated in this classification phase. "
        f"In strict accordance with Section 13 standards, **severity is never fabricated from classifier confidence scores**."
    )

    # ------------------ EXPLAINABILITY SECTION (Section 15) ------------------
    st.markdown("#### 👁️ Visual Explainability & Spatial Inspection")

    tab_orig, tab_overlay = st.tabs(["Original Image", "Analyzed Model Attention (Grad-CAM & Bounding Boxes)"])

    with tab_orig:
        st.image(original_image, caption="Original Farmer Upload (Unaltered RGB)", use_container_width=True)

    with tab_overlay:
        exp = result.explainability
        if exp.disease_heatmap and exp.disease_heatmap.startswith("data:image/jpeg;base64,"):
            b64_data = exp.disease_heatmap.split(",")[1]
            img_bytes = base64.b64decode(b64_data)
            overlay_pil = Image.open(io.BytesIO(img_bytes))
            st.image(overlay_pil, caption=f"Explainability Overlay ({exp.explanation_type})", use_container_width=True)
        elif exp.disease_heatmap and not exp.disease_heatmap.startswith("data:"):
            # Local file path
            try:
                st.image(exp.disease_heatmap, caption=f"Explainability Overlay ({exp.explanation_type})", use_container_width=True)
            except Exception:
                st.image(original_image, caption="Visual explanation file inaccessible.", use_container_width=True)
        elif exp.pest_boxes:
            # Draw pest bounding boxes onto copy
            from disease_pest_ai.inference.visualization import draw_pest_detections
            annotated_img = draw_pest_detections(original_image, result.pests.detections)
            st.image(annotated_img, caption="Pest Spatial Localization Bounding Boxes", use_container_width=True)
        else:
            st.image(original_image, caption="No visual explanation produced (Healthy / Bypassed).", use_container_width=True)

        st.caption("⚠️ *Visual explanation highlights model convolutional attention and spatial bounding boxes; it does not establish medical or biological causation.*")

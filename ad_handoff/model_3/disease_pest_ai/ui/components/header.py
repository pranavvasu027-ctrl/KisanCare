"""
UI Header, Pipeline Status, and Safety Banner Components (Sections 13, 16, 18).
"""

import streamlit as st


def render_header():
    """Renders the main title banner."""
    st.markdown(
        """
        <div style="text-align: center; padding: 1.2rem 0; border-bottom: 2px solid #2e7d32; margin-bottom: 1.5rem;">
            <h1 style="color: #1b5e20; margin-bottom: 0.2rem; font-size: 2.2rem; font-weight: 700;">
                🌾 AGRICULTURE AI
            </h1>
            <h3 style="color: #388e3c; margin-top: 0; font-size: 1.25rem; font-weight: 500;">
                Disease & Pest Detection System
            </h3>
            <p style="color: #616161; font-size: 0.9rem; margin-bottom: 0;">
                Pretrained Multimodal Diagnostics & Statutory CIB&RC Advisory Pipeline
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_pipeline_status():
    """Renders the compact architectural pipeline status block (Section 16)."""
    with st.container():
        st.markdown(
            """
            <div style="background-color: #f1f8e9; border: 1px solid #c8e6c9; border-radius: 6px; padding: 0.75rem 1rem; margin-bottom: 1.2rem; font-size: 0.88rem;">
                <div style="font-weight: 600; color: #2e7d32; margin-bottom: 0.4rem;">
                    Active System Pipeline Status:
                </div>
                <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 0.4rem; color: #37474f;">
                    <div><b>Disease Model:</b> <span style="color: #2e7d32;">✓ EfficientNetV2-S</span></div>
                    <div><b>Pest Detector:</b> <span style="color: #2e7d32;">✓ YOLO11s (IP102)</span></div>
                    <div><b>Crop Validation:</b> <span style="color: #2e7d32;">✓ Active</span></div>
                    <div><b>Treatment Engine:</b> <span style="color: #2e7d32;">✓ CIB&RC Registered</span></div>
                    <div><b>Knowledge Base:</b> <span style="color: #2e7d32;">✓ 2024-03-31 Register</span></div>
                    <div><b>Explainability:</b> <span style="color: #2e7d32;">✓ Grad-CAM + Bounding Boxes</span></div>
                    <div style="grid-column: 1 / -1; color: #78909c; font-size: 0.8rem; border-top: 1px dashed #cfd8dc; padding-top: 0.3rem; margin-top: 0.2rem;">
                        <b>Irrigation Module:</b> <i>Not part of this pipeline</i> (Disease and irrigation subsystems remain strictly decoupled).
                    </div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )


def render_persistent_safety_banner():
    """Renders mandatory statutory safety notices (Section 13)."""
    st.info(
        "🛡️ **Safety & Regulatory Notice:**\n"
        "- **AI-Assisted Diagnosis:** Machine predictions must be verified by visual field inspection before undertaking any chemical application.\n"
        "- **Label Compliance:** Always read and follow the physical product container label registered in your jurisdiction. Off-label usage is prohibited.\n"
        "- **Chemical Tank Mixes:** Never combine fungicides and insecticides without certified compatibility data.\n"
        "- **Expert Advisory:** Consult local agricultural extension officers or university pathologists for uncertain or severe infestations."
    )

"""
UI Provenance and Model Evaluation Components (Sections 14, 17, 18).
"""

from typing import Any, Dict
import streamlit as st

from disease_pest_ai.schemas.final_output import AgricultureDiseaseResult


def render_provenance_and_audit(result: AgricultureDiseaseResult):
    """
    Renders the complete audit log, model metadata, and latency breakdown (Section 14).
    """
    st.markdown("---")
    with st.expander("ℹ️ Sources & Model Information (Full Audit Trail)", expanded=False):
        prov = result.provenance

        col1, col2 = st.columns(2)

        with col1:
            st.markdown("##### 🧠 Machine Learning Models")
            st.write(f"**Disease Classifier:** `{prov.disease_model}`")
            st.write(f"**Disease Architecture:** `{prov.disease_model_version}`")
            st.write(f"**Pest Detector:** `{prov.pest_model or 'None'}`")
            st.write(f"**Pest Architecture:** `{prov.pest_model_version or 'N/A'}`")
            st.write(f"**Inference Hardware:** `{prov.device.upper()}`")

        with col2:
            st.markdown("##### 🏛️ Knowledge Base & Regulatory Sources")
            st.write(f"**Statutory Database:** `{prov.treatment_source}`")
            st.write(f"**Database Version:** `{prov.database_version}`")
            st.write(f"**Statutory Register Date:** `{prov.source_date}`")
            st.write(f"**Referenced Training Sets:** {', '.join(prov.dataset_sources)}")

        st.markdown("##### ⏱️ Component Latency Breakdown (CPU Execution)")
        bd = prov.latency_breakdown_ms
        if bd:
            lat_cols = st.columns(len(bd))
            for col, (k, v) in zip(lat_cols, bd.items()):
                clean_k = k.replace("_ms", "").replace("_", " ").title()
                col.metric(label=clean_k, value=f"{v:.1f} ms")


def render_model_evaluation_section():
    """
    Renders empirical evaluation results from project reports (Section 17).
    Strictly distinguishes benchmark results vs integration tests vs field validation.
    """
    with st.expander("📊 Model Evaluation & Empirical Benchmark Data", expanded=False):
        st.markdown(
            """
            This section reports **actual empirical benchmark results** documented in 
            [`reports/PHASE4_FUSION_BENCHMARK_REPORT.md`](file:///C:/Users/Atharva/.gemini/antigravity/scratch/disease_pest_ai/reports/PHASE4_FUSION_BENCHMARK_REPORT.md) 
            and [`test_data/final_benchmark_results.json`](file:///C:/Users/Atharva/.gemini/antigravity/scratch/disease_pest_ai/test_data/final_benchmark_results.json).
            """
        )

        st.markdown("##### Empirical Test Distinctions")
        st.info(
            "• **Benchmark Evaluation:** Evaluated on 8 multi-domain samples (Lab control, Field foliar, Trap sheets, Deliberate Mismatches).\n"
            "• **Integration Regression Test:** Automated 71-test pytest suite with a 100% pass rate.\n"
            "• **Field Validation Status:** Prototype tested on in-situ macro photographs. Multi-center agrochemical field validation trials are pending."
        )

        st.markdown("##### Performance Summary Across Configurations")
        st.markdown(
            """
            | Configuration | Average CPU Latency | Crop Mismatch Containment | Safety / Risk Profile |
            | :--- | :--- | :--- | :--- |
            | **Config A (Disease Only)** | 95.7 ms | 40.0% (Partial) | Blind to insect pests; trap cardboards misdiagnosed. |
            | **Config B (Pest Only)** | 299.1 ms | N/A | Blind to fungal, bacterial, and viral foliar blights. |
            | **Config C (Unvalidated Fusion)** | 394.8 ms | 0.0% (Uncontained) | High off-label chemical recommendation risk. |
            | **Config D (Validated Fusion)** | 396.3 ms | **100.0%** | Crop mismatch contained; trap sheets safely routed. |
            | **Config E (Full Pipeline)** | **846.0 ms** | **100.0%** | Full Section 12 output, CIB&RC verified, Grad-CAM. |
            """
        )

        st.markdown("##### Safety Metric Audits")
        st.write("• **Crop Mismatch Containment Rate:** `100.0%` (Zero chemical leakage on mismatched crops)")
        st.write("• **Unsupported Crop Rejection Rate:** `100.0%` (Immediate routing to manual review)")
        st.write("• **Ad-Hoc Chemical Tank Mixing Rate:** `0.0%` (Disease & pest treatments strictly decoupled)")
        st.write("• **Severity Invention Rate:** `0.0%` (Designated `unavailable`; never fabricated from confidence)")

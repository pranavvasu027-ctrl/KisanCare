"""
UI Treatment Recommendations and Warnings Component (Sections 12, 13, 18).
"""

from typing import List
import streamlit as st

from disease_pest_ai.schemas.final_output import AgricultureDiseaseResult
from disease_pest_ai.schemas.outputs import ChemicalCandidate, NonChemicalControl, RecommendationStatus


def render_treatment_recommendations(result: AgricultureDiseaseResult):
    """
    Renders verified CIB&RC treatment candidates and IPM non-chemical controls.
    Separates disease and pest treatment blocks (Sections 9, 10, 12).
    """
    st.markdown("---")
    st.subheader("3. Integrated Pest & Disease Management Advisory")

    tx_sec = result.treatment
    is_mismatch = not result.disease.crop_match
    is_healthy = result.disease.condition.lower() == "healthy" or result.disease.status == "healthy"

    if is_mismatch:
        st.warning(
            "🛑 **Chemical Recommendations Suppressed (Crop Mismatch):**\n\n"
            "Because the diagnosed condition does not biologically match the specified crop host, "
            "chemical recommendations have been completely withheld to prevent off-label pesticide application."
        )
        return

    if is_healthy:
        st.success(
            "🌱 **Healthy Foliage Confirmed:** No chemical intervention or pesticide application is required. "
            "Maintain routine agronomic monitoring and balanced fertilization."
        )
        # Show non-chemical IPM baseline if present
        if tx_sec.disease_recommendations and tx_sec.disease_recommendations.non_chemical_controls:
            with st.expander("Preventative Agronomic Hygiene Practices"):
                for nc in tx_sec.disease_recommendations.non_chemical_controls:
                    st.markdown(f"**• {nc.title}:** {nc.description}")
        return

    # Tabs for Disease Recommendations and Pest Recommendations
    tab_dis_tx, tab_pest_tx = st.tabs(["Foliar Disease Treatments (CIB&RC)", "Insect Pest Treatments (CIB&RC)"])

    # 1. Foliar Disease Treatments Tab
    with tab_dis_tx:
        dis_tx = tx_sec.disease_recommendations
        if dis_tx and dis_tx.status == RecommendationStatus.VERIFIED_CANDIDATES_FOUND:
            st.success(f"Verified CIB&RC Candidates Found for **{dis_tx.condition}** on **{dis_tx.crop}**")

            # Non-Chemical Controls
            if dis_tx.non_chemical_controls:
                st.markdown("##### 🌿 Non-Chemical Management & IPM Practices")
                for nc in dis_tx.non_chemical_controls:
                    with st.container():
                        st.markdown(f"**{nc.title}**")
                        st.write(nc.description)
                        st.caption(f"Source: {nc.source_title} ({nc.source_date})")

            # Chemical Candidates
            if dis_tx.chemical_candidates:
                st.markdown("##### 🧪 Registered Chemical Treatment Candidates")
                st.info("⚠️ **Statutory Label Disclaimer:** Always verify dosage and pre-harvest intervals against the physical container label registered in your state.")

                for idx, chem in enumerate(dis_tx.chemical_candidates, start=1):
                    with st.expander(f"Candidate {idx}: {chem.active_ingredient} ({chem.formulation or 'Approved Formulation'})"):
                        st.write(f"**Active Ingredient:** `{chem.active_ingredient}`")
                        st.write(f"**Approved Formulation:** `{chem.formulation or 'Refer to registered product'}`")
                        st.write(f"**Approved Label Crop:** `{chem.approved_crop}` | **Approved Target:** `{chem.approved_target}`")
                        st.write(f"**Statutory Dosage Guidance:** {chem.dose_information}")
                        if chem.safety_notes:
                            st.write(f"**Safety / Resistance Guidance:** {chem.safety_notes}")
                        st.caption(f"Register Authority: {chem.source_title} | Record Date: {chem.source_date} | Status: {chem.verification_status.upper()}")
        elif dis_tx and dis_tx.status == RecommendationStatus.MANUAL_REVIEW_REQUIRED:
            st.warning(f"⚠️ **Manual Review Required:** {dis_tx.reason_code or 'No registered chemical treatment found for this specific target in CIB&RC Major Uses register.'}")
            if dis_tx.non_chemical_controls:
                st.markdown("##### Non-Chemical Management Options:")
                for nc in dis_tx.non_chemical_controls:
                    st.write(f"• **{nc.title}:** {nc.description}")
        else:
            st.info("No foliar disease chemical treatments indicated.")

    # 2. Insect Pest Treatments Tab
    with tab_pest_tx:
        pest_tx = tx_sec.pest_recommendations
        if pest_tx and pest_tx.status == RecommendationStatus.VERIFIED_CANDIDATES_FOUND:
            st.success(f"Verified CIB&RC Candidates Found for **{pest_tx.condition}** on **{pest_tx.crop}**")

            # Non-Chemical Controls
            if pest_tx.non_chemical_controls:
                st.markdown("##### 🌿 IPM Biological & Cultural Controls")
                for nc in pest_tx.non_chemical_controls:
                    with st.container():
                        st.markdown(f"**{nc.title}**")
                        st.write(nc.description)
                        st.caption(f"Source: {nc.source_title} ({nc.source_date})")

            # Chemical Candidates
            if pest_tx.chemical_candidates:
                st.markdown("##### 🧪 Registered Insecticide Candidates")
                st.info("⚠️ **Statutory Label Disclaimer:** Chemical tank mixing with fungicides is NOT verified without certified tank mix approval.")

                for idx, chem in enumerate(pest_tx.chemical_candidates, start=1):
                    with st.expander(f"Candidate {idx}: {chem.active_ingredient} ({chem.formulation or 'Approved Formulation'})"):
                        st.write(f"**Active Ingredient:** `{chem.active_ingredient}`")
                        st.write(f"**Approved Formulation:** `{chem.formulation or 'Refer to registered product'}`")
                        st.write(f"**Approved Label Crop:** `{chem.approved_crop}` | **Approved Target:** `{chem.approved_target}`")
                        st.write(f"**Statutory Dosage Guidance:** {chem.dose_information}")
                        if chem.safety_notes:
                            st.write(f"**Safety / Waiting Period Guidance:** {chem.safety_notes}")
                        st.caption(f"Register Authority: {chem.source_title} | Record Date: {chem.source_date} | Status: {chem.verification_status.upper()}")
        elif pest_tx and pest_tx.status == RecommendationStatus.MANUAL_REVIEW_REQUIRED:
            st.warning(f"⚠️ **Manual Review Required for Pest:** {pest_tx.reason_code or 'Pest is outside verified statutory table.'}")
        else:
            st.info("No active insect pest infestation requiring chemical control detected.")


def render_aggregated_warnings(result: AgricultureDiseaseResult):
    """Renders consolidated system, domain, and agronomic warnings."""
    if result.warnings:
        st.markdown("---")
        st.subheader("4. Operational & Domain Advisories")
        for w in result.warnings:
            if "Domain Notice" in w or "Domain" in w:
                st.warning(f"🌐 {w}")
            elif "Crop Mismatch" in w or "Crop mismatch" in w:
                st.error(f"🛑 {w}")
            elif "Low Resolution" in w:
                st.warning(f"📐 {w}")
            else:
                st.info(f"ℹ️ {w}")

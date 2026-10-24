# Phase 2 — Deterministic Treatment Knowledge Base & Recommendation Engine Report

**Module**: `disease_pest_ai`  
**Phase**: Phase 2 Implementation & Verification  
**Date**: 2026-10-04  
**Operating Environment**: Windows / Python 3.11.9 / PyTorch 2.14.0+cpu  
**Primary Disease Engine**: `BiernyVR/crop-disease-classifier` (EfficientNetV2-S)  
**Database Version**: `1.0.0-20240331`  
**Engine Verdict**: **GREEN**

---

## Executive Summary

Phase 2 establishes a **100% deterministic, safety-first agronomic recommendation engine** that converts visual diagnostic outputs and user agronomic context into statutory CIB&RC chemical candidates, non-chemical Integrated Pest Management (IPM) practices, and end-to-end audit provenance.

No neural network predicts or invents pesticide names or dosages. No large language model (LLM) is used to synthesize treatment protocols. Where application information is not published in authoritative registers, the engine explicitly falls back to mandatory physical container label checks.

---

## A. Sources Investigated

1. **Central Insecticides Board & Registration Committee (CIB&RC)**:
   - Primary statutory publication: *"Major Uses of Pesticides (Registered under the Insecticides Act, 1968)"*.
   - Documents approved crops, approved target diseases/pests, chemical active ingredients, formulation percentages/types, and waiting periods (PHI).
2. **Directorate of Plant Protection, Quarantine & Storage (DPPQS)**:
   - *"DPPQS Integrated Pest Management (IPM) Package of Practices"*.
   - National standard guidelines for cultural, mechanical, and biological crop protection.
3. **National Research Centre for Integrated Pest Management (ICAR-NCIPM)**:
   - Technical bulletins on biocontrol agents (*Trichoderma viride*, *Trichogramma* parasitoids), sex pheromone traps, and economic threshold levels (ETL).
4. **Central Institute of Temperate Horticulture (ICAR-CITH), Srinagar**:
   - Technical guidelines on Apple Scab eradication, post-harvest orchard sanitation, and 5% urea spray floor protocols.
5. **National Research Centre for Grapes (ICAR-NRCG), Pune**:
   - Viticulture trunk disease advisories, pruning hygiene, and copper protectant schedules.
6. **Central Citrus Research Institute (ICAR-CCRI), Nagpur**:
   - Huanglongbing (Citrus Greening) vector suppression, orchard sanitation, and systemic foliar protection.

---

## B. Source Dates & Regulatory Currency

- **Statutory CIB&RC Register Date**: `2024-03-31` (As published on DPPQS portal).
- **DPPQS IPM Package Date**: `2022-06-15`.
- **ICAR Institute Advisories**: `2023-01-10` to `2023-04-12`.
- **Knowledge Base Verification Date**: `2026-10-04`.
- **Statutory Currency Warning**: Every recommendation payload automatically injects an immutable currency warning explicitly advising farmers and agronomists that the register is current up to 31/03/2024 and physical label verification is legally required.

---

## C. Knowledge-Base Architecture

The knowledge base is implemented with a normalized, relational, schema-validated structure:

```
disease_pest_ai/knowledge_base/
├── schema.json               <- Formal Draft 2020-12 JSON Schema
├── schema.py                 <- Pydantic v2 KBRecord model with dynamic source resolution
├── sources.json              <- Relational register of authoritative sources
├── treatments.json           <- 63 normalized records conforming to schema.json
├── normalization.py          <- Canonical crop, pathology, and active ingredient normalizer
├── repository.py             <- Indexed in-memory dual-key query layer
├── build_treatments_json.py  <- Idempotent database materialization script
└── build_db.py               <- Core record compilation script
```

### Relational Schema Key Attributes
- **Primary Key**: `id` (e.g., `CIBRC-CHM-TOM-EB-001`, `IPM-NC-TOM-EB-001`)
- **Foreign Key**: `source_id` referencing `sources.json` (`SRC-CIBRC-2024`, `SRC-DPPQS-IPM-2022`, etc.)
- **Lookup Index**: In-memory hash index mapping `(canonical_crop, canonical_condition)` tuples to record lists.

---

## D. Record Count

| Category | Record Count |
|---|---|
| **CIB&RC Registered Chemical Formulations** | 40 |
| **Official Non-Chemical IPM Protocols** | 23 |
| **Total Verified Records** | **63** |

---

## E. Supported Crops (15)

1. **Apple** (*Malus domestica*)
2. **Bell Pepper / Capsicum** (*Capsicum annuum*)
3. **Blueberry** (*Vaccinium corymbosum*)
4. **Cherry** (*Prunus avium*)
5. **Corn / Maize** (*Zea mays*)
6. **Cotton** (*Gossypium hirsutum*)
7. **Grape** (*Vitis vinifera*)
8. **Orange / Citrus** (*Citrus sinensis*)
9. **Peach** (*Prunus persica*)
10. **Potato** (*Solanum tuberosum*)
11. **Raspberry** (*Rubus idaeus*)
12. **Soybean** (*Glycine max*)
13. **Squash** (*Cucurbita pepo*)
14. **Strawberry** (*Fragaria ananassa*)
15. **Tomato** (*Solanum lycopersicum*)

---

## F. Supported Diseases (19)

Strict biological separation is maintained across all pathologies:
1. Apple Scab (*Venturia inaequalis*)
2. Black Rot (*Botryosphaeria obtusa* / *Guignardia bidwellii*)
3. Cedar Apple Rust (*Gymnosporangium juniperi-virginianae*)
4. Cercospora Leaf Spot / Gray Leaf Spot (*Cercospora zeae-maydis*)
5. Corn Common Rust (*Puccinia sorghi*)
6. Early Blight (*Alternaria solani*) — *Maintained strictly separate from Late Blight*
7. Esca / Black Measles (*Phaeomoniella* complex)
8. Huanglongbing / Citrus Greening (*Candidatus Liberibacter asiaticus*)
9. Late Blight (*Phytophthora infestans*) — *Maintained strictly separate from Early Blight*
10. Leaf Blight / Isariopsis Leaf Spot (*Pseudocercospora vitis*)
11. Leaf Mold (*Passalora fulva*)
12. Leaf Scorch (*Diplocarpon earlianum*)
13. Northern Leaf Blight (*Exserohilum turcicum*)
14. Powdery Mildew (*Podosphaera clandestina* / *P. xanthii*)
15. Septoria Leaf Spot (*Septoria lycopersici*)
16. Target Spot (*Corynespora cassiicola*)
17. Tomato Bacterial Spot (*Xanthomonas campestris pv. vesicatoria*)
18. Tomato Mosaic Virus (ToMV)
19. Tomato Yellow Leaf Curl Virus (TYLCV)

---

## G. Supported Pests (2)

1. **Cotton Bollworm Infestation** (*Helicoverpa armigera* / *Pectinophora gossypiella*):
   - Verified pheromone trap monitoring, *Trichogramma* biological control, and CIB&RC approved chemical foliar candidates.
2. **Spider Mites / Two-Spotted Spider Mite** (*Tetranychus urticae*):
   - Verified acaricidal management on Solanaceous crops.

---

## H. Matching & Ranking Logic

### 1. Dual-Key Validation
Treatments are returned if and only if:
$$\text{Canonical}(\text{Input Crop}) == \text{Record Approved Crop}$$
$$\text{AND}$$
$$\text{Canonical}(\text{Condition}) == \text{Record Approved Target}$$

### 2. Crop Mismatch Guard
If the vision model diagnoses a pathology characteristic of another crop (e.g. user says `Wheat`, but vision model detects `Tomato Early Blight`), the engine flags:
```json
{
  "status": "manual_review_required",
  "reason_code": "CROP_CONDITION_MISMATCH",
  "chemical_candidates": []
}
```
**Strictly 0 chemical candidates are returned during a crop mismatch.**

### 3. Candidate Ranking Protocol
Candidates are **not** ranked by neural network confidence or commercial bias. They follow strict agronomic resistance management rules:
1. **IPM Non-Chemical Controls First**: Sanitation, biocontrols, and cultural barriers are exposed prominently.
2. **Contact Protectants / Multi-Site Fungicides First**: FRAC Group M (Mancozeb, Captan, Copper) to minimize fungal resistance.
3. **Combination / Dual-Action Formulations Second**: Protectant + Systemic mixtures.
4. **Single-Site Systemic Chemicals Third**: Specific single-site actives (e.g. Triazoles / Strobilurins).

---

## I. Location Handling

- The user input `location_state` is preserved across all pipelines and provenance records.
- All CIB&RC registrations in the database carry `geographic_scope: "India"` (statutory national scope under the Insecticides Act, 1968).
- The engine does not fabricate unverified state-level restrictions, but warns that local agricultural university advisories should be consulted for district micro-climates.

---

## J. Growth-Stage Handling

- User-provided `growth_stage` is captured in the contextual audit payload.
- Because the statutory CIB&RC "Major Uses of Pesticides" register does not universally define growth-stage exclusions, the engine sets `stage_specific_guidance = "unavailable"` unless explicitly published.
- The engine appends an advisory warning directing the user to follow growth-stage restrictions detailed on the physical container leaflet.

---

## K. Safety Controls & Defaults

Every single recommendation enforces:
- `label_verification_required = True`: Mandatory physical check of the CIB&RC container label.
- `field_validation_required = True`: Mandatory sign-off by a local Krishi Vigyan Kendra (KVK) or extension officer.
- **Mandatory Safety Notes**: Standard PPE requirements, drift avoidance, pollinator warnings, and safe container disposal.
- **Dosage Integrity**: Numerical dosage is exposed only when present in statutory tables; otherwise defaults to: *"Application details unavailable in verified source. Follow the current registered product label."*
- **Strictly No Tank Mixes**: The engine strictly refuses to generate multi-chemical cocktail or tank-mixing recipes.

---

## L. Unknown & Unsupported Case Handling

The engine refuses to guess or interpolate. It emits explicit Section 13 reason codes:
- `UNSUPPORTED_CROP`: Crop not present in verified database.
- `UNSUPPORTED_CONDITION`: Pathology not indexed.
- `CROP_CONDITION_MISMATCH`: Conflict between user crop and vision diagnosis.
- `NO_VERIFIED_TREATMENT`: Recognized condition with no approved chemical in register.
- `LOW_MODEL_SCORE`: Vision model confidence below 40% operational threshold.
- `HEALTHY`: Healthy tissue returns `NO_TREATMENT_NEEDED_HEALTHY` and 0 synthetic chemicals.

---

## M. Test Verification Results

All **42 automated test cases** across `tests/` pass with 100% success rate:

```
============================= test session starts =============================
platform win32 -- Python 3.11.9, pytest-9.1.1
collected 42 items

test_adapters.py::test_efficientnet_adapter_loading_and_prediction     PASSED
test_adapters.py::test_efficientnet_adapter_crop_mismatch              PASSED
test_adapters.py::test_yolo_adapter_loading_and_prediction             PASSED
test_adapters.py::test_wadhwani_adapter_checkpoint_unavailability      PASSED
test_crop_validation.py::test_crop_normalization                       PASSED
test_crop_validation.py::test_crop_consistency_matches                 PASSED
test_crop_validation.py::test_crop_consistency_mismatches              PASSED
test_crop_validation.py::test_crop_consistency_none_inputs             PASSED
test_phase2_section19.py::test_01_valid_crop_disease_match             PASSED
test_phase2_section19.py::test_02_valid_crop_pest_match                PASSED
test_phase2_section19.py::test_03_crop_mismatch                        PASSED
test_phase2_section19.py::test_04_unsupported_disease                  PASSED
test_phase2_section19.py::test_05_unsupported_pest                     PASSED
test_phase2_section19.py::test_06_no_treatment_record                  PASSED
test_phase2_section19.py::test_07_multiple_valid_treatments            PASSED
test_phase2_section19.py::test_08_missing_dose_information             PASSED
test_phase2_section19.py::test_09_missing_stage_specific_information   PASSED
test_phase2_section19.py::test_10_location_state_input                 PASSED
test_phase2_section19.py::test_11_provenance_preservation              PASSED
test_phase2_section19.py::test_12_outdated_source_warning              PASSED
test_phase2_section19.py::test_13_low_confidence_diagnosis             PASSED
test_phase2_section19.py::test_14_healthy_plant                        PASSED
test_phase2_section19.py::test_15_unknown_condition                    PASSED
test_pipeline.py::test_pipeline_standard_prediction                    PASSED
test_pipeline.py::test_pipeline_missing_fields_validation_error        PASSED
test_pipeline.py::test_pipeline_model_override                         PASSED
test_schemas.py::test_input_contract_all_fields_present                PASSED
test_schemas.py::test_input_contract_missing_fields_raises_validation  PASSED
test_schemas.py::test_input_contract_empty_strings_rejected           PASSED
test_schemas.py::test_prediction_result_schema                         PASSED
test_treatment_engine.py::test_exact_crop_condition_match              PASSED
test_treatment_engine.py::test_crop_mismatch_blocks_chemicals          PASSED
test_treatment_engine.py::test_unsupported_disease_and_no_record       PASSED
test_treatment_engine.py::test_low_confidence_blocks_chemicals         PASSED
test_treatment_engine.py::test_multiple_valid_candidates_and_ipm_priority PASSED
test_treatment_engine.py::test_missing_numerical_dosage_falls_back     PASSED
test_treatment_engine.py::test_location_and_geographic_scope           PASSED
test_treatment_engine.py::test_growth_stage_handling_and_warning       PASSED
test_treatment_engine.py::test_outdated_source_warning                 PASSED
test_treatment_engine.py::test_healthy_plant_strictly_zero_chemicals   PASSED
test_treatment_engine.py::test_end_to_end_pipeline_with_treatment      PASSED
test_treatment_engine.py::test_end_to_end_pipeline_crop_mismatch       PASSED

============================= 42 passed in 48.28s =============================
```

---

## N. Provenance & Audit Traceability

Every end-to-end diagnosis produces a fully populated `AgricultureDiseaseResult` containing:
- `diagnosis`: Detected crop, condition, condition type, confidence score, and top-k predictions.
- `validation`: `crop_match`, `crop_mismatch`, `unsupported_condition`, and `reason_code`.
- `treatment`: Recommended chemical and IPM candidates with explicit status and safety notes.
- `provenance`: Vision model architecture, model version, execution latency, hardware backend, and list of referenced statutory source IDs and dates.
- `warnings`: Aggregated non-fatal operational, currency, and agronomic warnings.

---

## O. Limitations & Known Gaps

1. **WadhwaniAI Checkpoint**: Checkpoint remains unreleased by original authors. Handled via `pest_model_status = "unavailable"` without fake weights.
2. **Dynamic Regulatory Updates**: CIB&RC updates registers periodically; changes post 31/03/2024 require running the idempotent ingestion script.
3. **Tank-Mix Calculations**: Intentional design decision to NOT compute custom multi-pesticide tank mixtures to prevent chemical phytotoxicity and illegal off-label applications.

---

## P. Final Verdict

### **VERDICT: GREEN**
Phase 2 is fully implemented, verified, and ready for Phase 3.
- Deterministic knowledge base operational: **63 verified records**
- 100% test pass rate across 42 automated tests
- Zero LLM hallucinations, zero guessed dosages, zero unverified pesticide claims
- Complete Section 18 diagnostic breakdown and Section 19 test case validation

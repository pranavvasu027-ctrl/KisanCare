# KISANcare Soil Intelligence — Phase 6.1 Independent Audit Report

> **AUDIT SCOPE**: Independent technical, scientific, and layout audit of Phase 6 Reporting and Advisory modules.  
> **AUDIT PRINCIPLE**: Code and documentation inspection only. Zero codebase modifications executed during this audit run.  
> **AUDITED ARTIFACTS**:
> - `reporting/pdf_generator.py`
> - `reporting/report_builder.py`
> - `reporting/advisory.py`
> - `reporting/sample_illustrative_report.pdf`
> - `tests/test_pdf_report.py`
> - `tests/test_advisory.py`

---

## Executive Summary & Audit Verdict

This audit evaluated the scientific foundations, mathematical transformations, data integrity safeguards, PDF document validity, and automated test coverage of the Phase 6 reporting release.

### Final Audit Verdict:
**`CONDITIONAL PASS — internal testing only; listed issues must be addressed`**

**Justification**:
1. **Pass Criteria Met**:
   - The PDF generator produces valid ISO 32000-1 / PDF 1.4 binary documents with 100% byte-exact cross-reference (`xref`) tables.
   - Spatial coordinates of all text placement operators fall strictly within printable A4 page bounds with zero overlapping lines or margin clipping.
   - Provenance types (`MEASURED`, `FARMER_RECORDED`, `REGIONAL_MODEL`, `INSUFFICIENT_DATA`) remain strictly segregated across all sections.
   - The cumulative mass-balance ledger is clearly flagged as field surface flux and is not confused with extractable soil test available NPK.
   - The operational empirical prediction gate remains strictly `BLOCKED` (no future NPK values are fabricated).
   - Test suite reproducibility is verified at 61 passing tests in 0.017 seconds.
   - Strict file isolation is maintained: zero files outside `ml/soil_intelligence/` were created or modified.
2. **Conditions for Operational Release**:
   - Section title in the PDF report unconditionally describes baseline laboratory records as *"Certified"* even when certificate numbers or accreditation IDs are missing or unverified.
   - Crop yields have a lower bound check ($> 0$) but lack upper agronomic plausibility bounds ($> 20\text{ t/ha}$), leaving the mass-balance calculation vulnerable to extreme input typos.
   - While Olsen and Subbiah-Asija extraction protocols are correctly cited, specific authoritative citations for the pH band boundaries (e.g., USDA NRCS / ICAR) are omitted.
   - Verification of the PDF was performed via custom ISO 32000-1 binary inspection because no external third-party PDF parser (`pypdf`, `pdfminer`, `fitz`) is installed in the local environment.

---

## 1. Scientific Validity Audit

### A. Traceability of Nutrient Fertility Tiers
| Parameter | Method Cited in Code | Thresholds Applied | Authoritative Source | Appropriateness for Maharashtra Vertisols | Audit Status |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Available Nitrogen ($N$)** | Alkaline Permanganate Distillation | Low: $< 280\text{ kg/ha}$<br>Medium: $280 - 560\text{ kg/ha}$<br>High: $> 560\text{ kg/ha}$ | Subbiah & Asija (1956); ICAR / Muhr et al. (1965) | **Appropriate**: Standard Indian Soil Health Card criteria for active mineralized $N$. | **VERIFIED** |
| **Available Phosphorus ($P$)** | Olsen $0.5\text{M NaHCO}_3$ ($\text{pH } 8.5$) | Low: $< 10.0\text{ kg P/ha}$ ($22.9\text{ kg } P_2O_5$)<br>Medium: $10.0 - 24.4\text{ kg P/ha}$<br>High: $> 24.4\text{ kg P/ha}$ ($55.9\text{ kg } P_2O_5$) | Olsen et al. (1954); Tandon (2004) | **Appropriate**: Essential for calcareous, alkaline black soils ($\text{pH} > 7.5$) where Bray-1 extraction is invalid due to acid neutralization by $\text{CaCO}_3$. | **VERIFIED** |
| **Available Potassium ($K$)** | Neutral $1\text{N NH}_4\text{OAc}$ Flame Photometry | Low: $< 119.5\text{ kg K/ha}$ ($144\text{ kg } K_2O$)<br>Medium: $119.5 - 278.9\text{ kg K/ha}$<br>High: $> 278.9\text{ kg K/ha}$ ($336\text{ kg } K_2O$) | Hanway & Heidel (1952); Muhr et al. (1965) | **Appropriate**: Neutral ammonium acetate extracts exchangeable and water-soluble potassium. Smectitic Vertisols in Maharashtra frequently register in the High tier ($> 300\text{ kg } K_2O$). | **VERIFIED** |
| **Soil Reaction ($\text{pH}$)** | 1:2 / 1:2.5 Potentiometric Suspension | Strongly Acidic: $< 5.5$<br>Moderately Acidic: $5.5 - 6.5$<br>Neutral: $6.5 - 7.5$<br>Moderately Alkaline: $7.5 - 8.5$<br>Strongly Alkaline: $> 8.5$ | Cited as "Standard 1:2 / 1:2.5 Method" | **Appropriate**: Aligns with ICAR and USDA NRCS soil survey classification guidelines. However, formal bibliographic citation of the tier cutoffs is omitted. | **PARTIALLY VERIFIED** (Citation incomplete) |
| **Organic Carbon ($\text{OC}$)** | Walkley-Black Wet Oxidation | Low: $< 0.50\%$<br>Medium: $0.50 - 0.75\%$<br>High: $> 0.75\%$ | Walkley & Black (1934); Muhr et al. (1965) | **Appropriate**: Standard benchmark across Indian semi-arid agro-ecosystems. | **VERIFIED** |

### B. Treatment of Soil-Test Concentration vs. Total Profile Stocks
- **Finding**: The reporting pipeline consistently avoids treating available soil test values as total nutrient profile reserves.
- **Evidence**: In `reporting/report_builder.py` and `reporting/pdf_generator.py`, values are explicitly described as *"Available (extractable) pool in the 0–15 cm plow depth"*. Section 3 explicitly alerts:
  > *"CRITICAL NOTE: Net mass-balance represents field surface flux. It DOES NOT equal extractable soil available NPK. Soil test values depend on soil buffering, mineral fixation, microbial cycling, and leaching losses."*

### C. Unit & Stoichiometric Conversions Audit
1. **$P_2O_5 \to P$**:
   $$\text{Factor} = \frac{2 \times 30.973762}{141.944524} = 0.4364205\dots \quad (\text{Code uses } 0.4364205)$$
   **Status**: Mathematically exact.
2. **$K_2O \to K$**:
   $$\text{Factor} = \frac{2 \times 39.0983}{94.1960} = 0.8301552\dots \quad (\text{Code uses } 0.8301552)$$
   **Status**: Mathematically exact.
3. **$\text{ppm} \to \text{kg/ha}$ Gravimetric Spatial Conversion**:
   $$\text{Soil mass per hectare} = 10,000\text{ m}^2 \times 0.15\text{ m} \times 1,330\text{ kg/m}^3 = 1,995,000\text{ kg} \implies \text{Factor} = 1.9950$$
   **Status**: Code applies $1.9950\text{ kg/ha}$ per $\text{mg/kg}$ and logs:
   `"ppm -> kg/ha via depth 0.15m & bulk density 1.33g/cm3 (factor 1.9950)"`. This explicitly records the underlying bulk density and topsoil depth assumptions.

---

## 2. PDF Correctness Audit

### A. Environment Limitation Disclosure
- **Tooling Limitation**: Neither `pypdf`, `pdfminer`, `fitz` (PyMuPDF), nor `poppler-utils` is installed in the local Python 3.11 environment.
- **Audit Methodology**: An independent binary parser script was authored using Python's standard library to inspect the generated `sample_illustrative_report.pdf` according to ISO 32000-1 specifications.

### B. Independent Structural Audit Results
1. **Binary Header & Magic Bytes**:
   - Byte offset 0: `%PDF-1.4\n%\xe2\xe3\xcf\xd3\n` (Compliant with ISO 32000-1 §7.5.2).
2. **Cross-Reference Table (`xref`)**:
   - `startxref` pointer: Offset `14243`.
   - Table entries: 9 objects (Catalog, Pages tree, 4 Type1 Fonts, 1 Page, 1 Content stream).
   - **Byte Offset Verification**: Every object header (`X 0 obj`) matches its registered byte offset in the `xref` table to the exact byte.
3. **Page Geometry & MediaBox**:
   - `MediaBox`: `[0 0 595.28 841.89]` (Strict ISO A4 portrait dimensions: $210 \times 297\text{ mm}$).
4. **Coordinate Bounds & Clipping**:
   - Total text placement commands audited: **116 text blocks**.
   - Horizontal bounds: $x_{\min} = 36.00\text{ pt}$ (left margin), $x_{\max} = 504.28\text{ pt}$ (right margin).
   - Vertical bounds: $y_{\min} = 47.00\text{ pt}$ (footer line), $y_{\max} = 781.89\text{ pt}$ (header banner).
   - **Clipping Status**: Zero out-of-bounds coordinates. Zero text overlaps detected at identical $(x, y)$ positions.
5. **Character Encoding & Glyph Mapping**:
   - Fonts used: `/Helvetica`, `/Helvetica-Bold`, `/Helvetica-Oblique`, `/Courier`.
   - Character encoding: `/WinAnsiEncoding`.
   - All scientific symbols are mapped to clean standard ASCII (e.g. `+/-` for $\pm$, `P2O5` for $P_2O_5$, `x` for $\times$). Zero unmapped Unicode replacement symbols (`?`) were detected in text strings.
6. **Multi-Page Pagination**:
   - Verified via `test_long_multi_year_timelines_span_multiple_pages`: Timelines exceeding 20 events automatically trigger vertical overflow page breaks, maintaining dynamic page numbering (`Page 1 of 2`, `Page 2 of 2`) and repeated running headers/footers.

---

## 3. Data Integrity & Privacy Audit

### A. Non-Zero Treatment of Missing Data
- **Audit Check**: Does missing management data default to zero flux?
- **Finding**: **Verified**.
  - In `AgronomicDepletionEngine.compile_cumulative_ledger`, missing crop records trigger `FLAG_UNRECORDED_CROPS`, penalize input coverage by $40\%$, and expand $N, P, K$ uncertainty variances by $40^2, 8^2, 35^2\text{ kg}^2/\text{ha}^2$ rather than assuming zero depletion.
  - In `PlotTimelineManager.assess_data_sufficiency`, a baseline $> 36\text{ months}$ old with zero recorded management events forces `is_sufficient = False` and triggers safe abstention (`INSUFFICIENT_DATA`).
  - In `pdf_generator.py`, missing optional parameters (such as EC or Organic Carbon) are omitted from the table rather than displayed as $0.0$.

### B. Consistent Provenance Labeling Across Report Sections
Every report section displays an explicit provenance badge:
- Section 1: `PROVENANCE: MEASURED`
- Section 2: `PROVENANCE: FARMER_RECORDED`
- Section 3: `BOOKKEEPING ONLY`
- Section 4: `STATUS: UNCALIBRATED_HEURISTIC_BOUND`
- Section 5: `STATUS: INSUFFICIENT_DATA (Operational Empirical Prediction Gated)`
- Section 6: `GENERAL_EDUCATIONAL_GUIDANCE`

### C. Privacy Protection & Accreditation Claims Audit
1. **Identifier Masking**:
   - Plot identifier `PLOT_MH_LAT_881` is consistently masked as `PLOT_MH_LAT_****81`.
   - Farm identifier `FARM_LAT_01` is masked as `FARM_LA_****01`.
2. **Laboratory Accreditation Assumption Risk**:
   - **Finding (Defect D-01)**: In `reporting/pdf_generator.py` line 253, Section 1 is titled:
     `"1. Certified Laboratory Baseline Soil Measurements"`.
   - **Impact**: If a user uploads an uncertified laboratory test or an informal scan where `lab_certificate_no` is missing or unverified, the report heading still claims the measurement is *"Certified"*. This could mislead a farmer or agronomist into assuming the report underwent NABL/government accreditation verification.

---

## 4. Test Review & Gap Analysis

### A. Test Suite Reproducibility
- **Command**:
  ```powershell
  & "$env:LOCALAPPDATA\Programs\Python\Python311\python.exe" -m unittest discover -s "KISANcare/kisan-care/ml/soil_intelligence/tests" -t "KISANcare/kisan-care" -p "test_*.py" -v
  ```
- **Execution Time**: 0.017 seconds.
- **Result**: **61 tests passed, 0 failures, 0 errors, 0 skipped.**
  - `test_data_readiness.py`: 4 passed
  - `test_ocr_extraction.py`: 4 passed
  - `test_schemas.py`: 12 passed
  - `test_timeline.py`: 10 passed
  - `test_predictor.py`: 17 passed
  - `test_advisory.py`: 6 passed
  - `test_pdf_report.py`: 8 passed

### B. Identified Missing Negative Tests
1. **Extreme Harvest Yield Input**:
   - `AgronomicDepletionEngine.calculate_crop_removal` validates `if yield_tons_ha <= 0: raise ValueError(...)`, but has no upper agronomic boundary check. If an erroneous yield of $500\text{ t/ha}$ is entered, it calculates an unphysical removal of $12,250\text{ kg N/ha}$.
2. **Reverse Temporal Query**:
   - No negative test exists verifying behavior when a prediction query date precedes the baseline test date ($T_{\text{target}} < T_{\text{baseline}}$).
3. **Excessive Fertilizer Application Rate**:
   - `calculate_fertilizer_input` checks `if application_rate_kg_ha <= 0: raise ValueError(...)`, but lacks an upper threshold (e.g. $> 5,000\text{ kg/ha}$).
4. **PDF Special Character / String Injection**:
   - While `_escape_pdf_text` escapes parentheses and backslashes, a dedicated unit test verifying injection resilience against malicious string payloads (e.g. `") Tj /F2 20 Tf ("`) is missing.

---

## 5. File Isolation Confirmation

A recursive workspace scan verified that **zero files outside `kisan-care/ml/soil_intelligence/` were modified or created**. No existing KISANcare application models, databases, or UI files were touched.

---

## 6. Detailed Audit Findings & Remediation Plan

### Finding D-01: Section Title Falsely Implies Laboratory Certification
- **Severity**: **MODERATE**
- **Affected File / Function**: `reporting/pdf_generator.py` -> `_render_measured_parameters()` (line 253)
- **Evidence**:
  ```python
  self._render_section_heading("1. Certified Laboratory Baseline Soil Measurements", "PROVENANCE: MEASURED")
  ```
- **Impact**: Any laboratory report (even an unverified OCR draft where `lab_certificate_no` is missing or `extraction_confidence < 1.0`) is labeled in the PDF heading as *"Certified"*.
- **Recommended Remediation**: Change the section heading to `"1. Physical Laboratory Baseline Soil Measurements"`. Add a conditional subtitle badge: display `"[CERTIFIED ACCREDITED]"` only if `lab_certificate_no` and `lab_accreditation_id` are populated and verified; otherwise display `"[UNVERIFIED CERTIFICATE NUMBER]"`.

---

### Finding D-02: Missing Upper Agronomic Bounds on Crop Harvest Yield
- **Severity**: **MODERATE**
- **Affected File / Function**: `timeline/agronomic_depletion.py` -> `calculate_crop_removal()` (line 367)
- **Evidence**:
  ```python
  if yield_tons_ha <= 0:
      raise ValueError(f"Harvest yield must be strictly positive: {yield_tons_ha}")
  # No check for yield_tons_ha > MAX_PLAUSIBLE_YIELD
  ```
- **Impact**: A typographical input error (e.g. entering $50\text{ t/ha}$ instead of $5.0\text{ t/ha}$ for maize) results in massive over-depletion in the mass-balance ledger ($1,100\text{ kg N}$ removal).
- **Recommended Remediation**: Add upper agronomic plausibility boundaries per crop (e.g., wheat/rice $\le 15\text{ t/ha}$, soybean/pulses $\le 8\text{ t/ha}$, sugarcane $\le 250\text{ t/ha}$). Flag yields exceeding these bounds as `SUSPICIOUS_HIGH_YIELD` requiring confirmation.

---

### Finding D-03: Missing Authoritative Citation for Soil Reaction (pH) Bands
- **Severity**: **MINOR**
- **Affected File / Function**: `reporting/advisory.py` -> `classify_ph()` (line 203)
- **Evidence**:
  ```python
  scientific_reference="Standard 1:2 / 1:2.5 Soil-Water Potentiometric Method"
  ```
- **Impact**: While the potentiometric laboratory method is cited, the authoritative source for the agricultural classification bands ($< 5.5$ strongly acidic, $6.5-7.5$ neutral, $> 8.5$ strongly alkaline) is not cited.
- **Recommended Remediation**: Update `scientific_reference` to cite both the analytical protocol and the classification authority: `"Standard 1:2.5 Soil-Water Potentiometric Method (Jackson 1973; USDA Soil Survey Manual / ICAR Guidelines)"`.

---

### Finding D-04: Test Suite Relies on Internal Text Stream Decoding
- **Severity**: **MINOR**
- **Affected File / Function**: `tests/test_pdf_report.py`
- **Evidence**:
  `test_pdf_report.py` inspects the raw byte stream output of `SoilIntelligencePDFGenerator` because no external PDF parser is installed in the local environment.
- **Impact**: While byte offset integrity and coordinate bounding were independently verified via custom ISO 32000-1 binary parsing in `scratch/audit_pdf.py`, automated continuous integration tests lack validation against an external reference PDF rendering engine (such as PyMuPDF or Ghostscript).
- **Recommended Remediation**: When external dependencies are authorized, integrate `pypdf` or `pymupdf` into the test suite to verify rendered visual elements.

---

## Summary of Findings & Recommended Actions

| Finding ID | Severity | Description | Action Required |
| :--- | :--- | :--- | :--- |
| **D-01** | **MODERATE** | Section heading unconditionally labels baseline as "Certified" | Retitle to "Physical Laboratory Baseline" and gate "Certified" badge on verified accreditation ID |
| **D-02** | **MODERATE** | Crop removal calculation lacks upper yield plausibility boundary | Implement upper yield bounds ($15\text{ t/ha}$ cereals, $8\text{ t/ha}$ legumes) |
| **D-03** | **MINOR** | pH classification citations lack formal taxonomic reference | Add USDA / ICAR Jackson (1973) reference |
| **D-04** | **MINOR** | PDF tests inspect raw byte stream due to lack of local parser | Add third-party PDF reader validation when environment approval is granted |

---

### Final Determination

The Phase 6 reporting architecture is scientifically disciplined, transparent regarding uncertainties, and mathematically sound. It refuses to fabricate predictions while the operational gate is blocked. With the audit verdict of **`CONDITIONAL PASS`**, the module is approved for internal demonstration, pilot testing, and agronomic review. 

**Per strict instructions, no files were modified during this audit run. Remediation of D-01 through D-04 will be executed upon Phase 6.2 authorization.**

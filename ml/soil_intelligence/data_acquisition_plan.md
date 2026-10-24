# KISANcare Soil Intelligence — Genuine Longitudinal Soil Data Acquisition Plan

> **DOCUMENT STATUS**: Official Engineering & Scientific Protocol  
> **PURPOSE**: Specifies the precise requirements, governance, sampling design, and verification protocol to acquire accredited longitudinal soil laboratory datasets for KISANcare Soil Intelligence V1.  
> **RULE**: Do NOT scrape restricted portals, fabricate data records, or claim data access until formally verified and authorized.

---

## 1. Objective & Scope

Empirical machine-learning models predicting available soil Nitrogen ($N$), Phosphorus ($P$), and Potassium ($K$) over multi-year horizons require genuine longitudinal field ground truth:
$$\text{Ground Truth Record} = \{ (P_i, t_1, \mathbf{M}_1), (P_i, \mathbf{E}_{t_1 \to t_2}), (P_i, t_2, \mathbf{M}_2) \}$$
where:
- $P_i$ is a persistent, geo-referenced plot boundary.
- $t_1, t_2$ are distinct sampling dates ($t_2 - t_1 \ge 1\text{ full crop season}$, typically 6–36 months).
- $\mathbf{M}_1, \mathbf{M}_2$ are certified physical laboratory soil test measurements.
- $\mathbf{E}_{t_1 \to t_2}$ are complete, dated farm management records logged between $t_1$ and $t_2$.

Cross-sectional datasets (such as single-cycle Soil Health Card exports) and synthetic datasets are permanently blocked from serving as longitudinal ground truth.

---

## 2. Required Fields for Repeated Soil Laboratory Measurements

To qualify for empirical model training and leakage-safe validation, every paired measurement must capture the following attributes without omission:

### A. Plot Identity & Spatial Integrity
| Field Name | Type | Description | Validation Rule |
| :--- | :--- | :--- | :--- |
| `plot_id` | String | Unique, immutable plot identifier | Must match across repeated visits ($t_1, t_2$) |
| `farm_id` | String | Farmer / holding identifier | Required for grouped cluster splits |
| `state` | String | State (e.g., Maharashtra) | Standard ISO code / name |
| `district` | String | District (e.g., Latur, Osmanabad) | Standard administrative name |
| `taluka` | String | Sub-district / Taluka | Standard administrative name |
| `village` | String | Revenue village | Standard village code / name |
| `survey_number` | String | Revenue survey / Gat number | Official land record identifier |
| `centroid_latitude` | Float | GPS Latitude (WGS84, decimal degrees) | Precision $\ge 5$ decimal places |
| `centroid_longitude`| Float | GPS Longitude (WGS84, decimal degrees)| Precision $\ge 5$ decimal places |
| `plot_area_ha` | Float | Physical plot area in hectares | Strict $0.1 \le \text{area} \le 50.0\text{ ha}$ |

### B. Soil Sampling Protocol & Laboratory Quality Control
| Field Name | Type | Description | Required Standard / Acceptable Range |
| :--- | :--- | :--- | :--- |
| `sample_id` | String | Unique physical soil sample ID | Must be traceable to physical laboratory sample |
| `sampling_date` | Date | Exact date sample was collected (`YYYY-MM-DD`)| Valid calendar date |
| `sampling_depth_top_cm` | Float | Upper depth of core (cm) | Standard: $0.0\text{ cm}$ |
| `sampling_depth_bottom_cm` | Float | Lower depth of core (cm) | Standard: $15.0\text{ cm}$ (plow depth layer) |
| `sampling_method` | String | Sampling pattern | Composite core (10–15 sub-samples in 'V' pattern) |
| `lab_name` | String | Accredited testing facility | ICAR / NABL / State Dept accredited lab |
| `lab_certificate_no` | String | Official report / certificate number | Traceable audit reference |
| `lab_accreditation_id` | String | NABL / Dept registration number | Verifiable accreditation |
| `analysis_date` | Date | Date chemical extraction performed | Within 30 days of sampling date |

### C. Chemical Parameters, Analytical Methods & Units
All nutrient concentrations must record both the verbatim reported value and the standard analytical protocol:

| Parameter | Verbatim Unit Stated | Standard Analytical Method | Elemental Standard |
| :--- | :--- | :--- | :--- |
| **Available Nitrogen** | $\text{kg/ha}$ or $\text{mg/kg}$ | Alkaline Permanganate (Subbiah & Asija 1956) | Elemental $N$ ($\text{kg/ha}$) |
| **Available Phosphorus**| $\text{kg/ha}$ or $\text{mg/kg}$ ($P$ or $P_2O_5$) | Olsen 0.5M $\text{NaHCO}_3$ ($\text{pH} \ge 6.5$) / Bray-1 ($\text{pH} < 6.5$) | Elemental $P$ ($\text{kg/ha}$) |
| **Available Potassium** | $\text{kg/ha}$ or $\text{mg/kg}$ ($K$ or $K_2O$) | Neutral 1N Ammonium Acetate Flame Photometry | Elemental $K$ ($\text{kg/ha}$) |
| **Soil Reaction ($\text{pH}$)** | Standard scale ($0–14$) | Potentiometric 1:2 or 1:2.5 soil-water suspension | Standard $\text{pH}$ |
| **Electrical Cond. ($\text{EC}$)**| $\text{dS/m}$ | Conductivity bridge 1:2 or 1:2.5 suspension | Standard $\text{dS/m}$ |
| **Organic Carbon ($\text{OC}$)**| $\%$ | Walkley-Black wet oxidation or Dumas dry combustion | $\%$ by weight |

---

## 3. Management Records Between Laboratory Tests ($\mathbf{E}_{t_1 \to t_2}$)

A longitudinal pair is unusable if the intervening farm management is unrecorded. The following events must be logged:

1. **Crop Cycles & Yields**:
   - Crop species, cultivar/variety, sowing date, and harvest date.
   - Harvested economic yield ($\text{metric tons/ha}$).
   - Crop residue management: Straw retained/incorporated vs. burned vs. removed.
2. **Fertilizer Applications**:
   - Application date and growth stage (basal, top-dressing).
   - Commercial fertilizer grade name (e.g., Urea 46-0-0, DAP 18-46-0, MOP 0-0-60, 10-26-26).
   - Exact physical quantity applied ($\text{kg/ha}$).
3. **Organic Amendments & Manures**:
   - Manure type: Farmyard Manure (FYM), Vermicompost, Poultry Manure, Pressmud.
   - Moisture condition and quantity applied ($\text{metric tons/ha}$).
4. **Irrigation & Water Regime**:
   - Irrigation source (rainfed, tube well, canal, drip).
   - Number of irrigation irrigations and estimated depth ($\text{mm}$).
5. **Weather Data Context**:
   - Cumulative seasonal precipitation ($\text{mm}$) during the interval.
   - Mean seasonal temperature ($^\circ\text{C}$).

---

## 4. Data Provenance, Consent, Privacy & Permitted Use

1. **Farmer Informed Consent**:
   - Individual farmer data must be collected with signed or verified digital informed consent under the Digital Personal Data Protection (DPDP) Act.
   - Consent must explicitly authorize agricultural advisory modeling and anonymized model evaluation.
2. **PII Anonymization**:
   - Farmer personal names, phone numbers, Aadhaar numbers, and national IDs must be stripped before entering the ML pipeline.
   - Plot identifiers are pseudonymized with irreversible cryptographic salt hashes (e.g., `MH-LAT-2024-X8F21`).
3. **Data Licensing & Attribution**:
   - Official institutional trials (ICAR / KVK / SAU) must have documented written data-sharing agreements (MOU or Academic Research License).
   - Proprietary or restricted data must not be scraped or ingested without verifiable written permission.

---

## 5. Legitimate Sources of Maharashtra Soil Data & Verification Protocol

| Source Category | Potential Provider / Institution | Accessibility Status | Mandatory Verification Before Ingestion |
| :--- | :--- | :--- | :--- |
| **State Agricultural Universities (SAUs)** | Vasantrao Naik Marathwada Krishi Vidyapeeth (VNMKV), Parbhani; MPKV Rahuri | **Potential** (requires formal research collaboration / MOU) | Verify trial design, GPS repeatability, soil sampling protocol, and official analytical records. |
| **ICAR Institutes & KVKs** | ICAR-NBSS&LUP (Nagpur); District Krishi Vigyan Kendras (e.g., KVK Latur) | **Potential** (formal institutional data request) | Verify plot boundary permanence, consistency of extraction reagents, and complete crop-fertilizer ledgers. |
| **All India Coordinated Research Projects (AICRP)** | AICRP on Long-Term Fertilizer Experiments (LTFE); AICRP for Dryland Agriculture | **Potential** (published research data & annual reports) | Verify individual plot numbers, treatment layouts, and raw analytical tables (not just pooled treatment means). |
| **Contract Farming / Agritech Field Trials** | FPO / Corporate agronomy trials with certified lab testing | **Potential** (commercial agreement required) | Audit lab accreditation, verify chain of custody, and ensure farmer consent. |
| **Central Soil Health Card Portal** | Ministry of Agriculture & Farmers Welfare, GoI (`soilhealth.dac.gov.in`) | **Accessible** (cross-sectional public exports) | **CANNOT be used as longitudinal ground truth**. Single-point exports lack paired re-tests on the same plot. |

---

## 6. Illustrative Data Schema & Placeholder Dictionary

> [!IMPORTANT]
> The following records are **illustrative synthetic placeholders** provided strictly to demonstrate the required JSON schema format. They are **NOT** genuine observations and must **NEVER** be ingested into model training.

```json
{
  "$schema": "https://kisancare.in/schemas/soil_longitudinal_pair_v1.json",
  "pair_id": "PAIR-MH-LAT-0001",
  "plot": {
    "plot_id": "PLOT-PLACEHOLDER-001",
    "district": "Latur",
    "taluka": "Ausa",
    "village": "SampleVillage",
    "centroid_gps": [18.25123, 76.49124],
    "soil_texture_class": "Clay Loam",
    "area_ha": 1.20
  },
  "baseline_measurement_t1": {
    "sample_id": "LAB-2023-T1-SAMPLE",
    "sample_date": "2023-05-20",
    "sampling_depth_cm": [0.0, 15.0],
    "lab_name": "Accredited Soil Laboratory Example",
    "lab_certificate_no": "CERT-2023-0001",
    "available_n": { "value": 220.0, "unit": "kg/ha", "form": "ELEMENTAL_N", "method": "Alkaline Permanganate" },
    "available_p": { "value": 14.5, "unit": "kg/ha", "form": "OXIDE_P2O5", "method": "Olsen NaHCO3" },
    "available_k": { "value": 310.0, "unit": "kg/ha", "form": "OXIDE_K2O", "method": "Neutral NH4OAc" },
    "ph": 7.6,
    "ec_ds_m": 0.28,
    "oc_pct": 0.48
  },
  "intervening_management_events": [
    {
      "event_type": "CROP_CYCLE",
      "crop_name": "Soybean",
      "sowing_date": "2023-06-25",
      "harvest_date": "2023-10-10",
      "yield_tons_ha": 2.1,
      "residue_retained": true,
      "fertilizers_applied": [
        { "name": "DAP", "rate_kg_ha": 75.0, "application_date": "2023-06-25" }
      ]
    },
    {
      "event_type": "CROP_CYCLE",
      "crop_name": "Gram (Chickpea)",
      "sowing_date": "2023-11-05",
      "harvest_date": "2024-02-28",
      "yield_tons_ha": 1.4,
      "residue_retained": true,
      "fertilizers_applied": []
    }
  ],
  "followup_measurement_t2": {
    "sample_id": "LAB-2024-T2-SAMPLE",
    "sample_date": "2024-05-15",
    "sampling_depth_cm": [0.0, 15.0],
    "lab_name": "Accredited Soil Laboratory Example",
    "lab_certificate_no": "CERT-2024-0042",
    "available_n": { "value": 235.0, "unit": "kg/ha", "form": "ELEMENTAL_N", "method": "Alkaline Permanganate" },
    "available_p": { "value": 16.0, "unit": "kg/ha", "form": "OXIDE_P2O5", "method": "Olsen NaHCO3" },
    "available_k": { "value": 325.0, "unit": "kg/ha", "form": "OXIDE_K2O", "method": "Neutral NH4OAc" },
    "ph": 7.7,
    "ec_ds_m": 0.30,
    "oc_pct": 0.50
  }
}
```

---

## 7. Missing-Data Handling & Quality Checks

Prior to accepting any field pair into the candidate dataset:
1. **Zero-Variance Rejection**: Check for automated or repeated identical values across distinct plots (identifies copy-paste fraud).
2. **Stoichiometric Feasibility**: Verify that Organic Carbon correlates plausibly with Available Nitrogen ($N \approx 0.05 \text{ to } 0.15 \times \text{OC}_{\text{total}}$). Extreme contradictions trigger manual agronomist audit.
3. **Plenitude Filter**: If either $N, P, K$, or $\text{pH}$ is missing at $t_1$ or $t_2$, the pair is rejected from evaluation.
4. **Temporal Gap Check**: If $t_2 - t_1 < 120\text{ days}$ (insufficient time for agronomic response) or $> 1095\text{ days}$ ($> 3\text{ years}$ without intermediate tests), flag for review.

---

## 8. Pilot Collection Plan & Statistical Sample-Size Determination

Rather than arbitrarily assuming 50–100 plots guarantees statistical validity, the collection strategy follows a 2-stage design:

### Stage 1: Phase 1 Pilot Field Trial ($N = 25\text{ plots}$)
- **Target Geography**: 25 farmer plots across 3 adjacent talukas in Latur district, Maharashtra (Vertisol / Black cotton soil).
- **Crops Monitored**: Kharif Soybean followed by Rabi Chickpea/Wheat.
- **Pilot Objective**:
  1. Measure empirical spatial variance ($\sigma_{\text{plot}}^2$) and analytical inter-lab measurement variance ($\sigma_{\text{lab}}^2$).
  2. Measure farmer logging completeness rate (percentage of farmers who record all fertilizer and harvest dates).
  3. Validate GPS repeatability of field core collection ($< 5\text{ meter}$ error radius).

### Stage 2: Power-Based Sample-Size Calculation for Final Model Evaluation
To validate that $\ge 80\%$ of predictions fall within tolerance with statistical confidence ($1 - \beta = 0.90$, $\alpha = 0.05$):
$$n = \left( \frac{Z_{1 - \alpha/2} \sqrt{p_0(1-p_0)} + Z_{1 - \beta}\sqrt{p_1(1-p_1)}}{p_1 - p_0} \right)^2$$
where $p_0 = 0.70$ (unacceptable baseline rate) and $p_1 = 0.80$ (target tolerance rate).
- For a one-sided binomial test with power $90\%$, minimum required independent test holdouts:
  $$n_{\text{holdout}} \ge 165 \text{ verified, independent longitudinal pairs}.$$
- Accounting for a $20\%$ farmer drop-out or incomplete logging rate, the total enrolled cohort must be:
  $$N_{\text{enrolled}} \ge 210 \text{ plots across varied soil textures and agro-climatic zones}.$$

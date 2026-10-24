# Research Assessment: Maharashtra Soil Health Card Cross-Sectional Dataset

**Dataset**: `data/npk/raw/raw_shc_maharashtra.csv` (7,396 rows)  
**Origin**: Government of India Soil Health Card (SHC) Portal Export (Cycle 2016–17)  
**Geography**: Maharashtra (Latur District, Ahemadpur / Ahmadpur Block)  
**Evaluator**: KISANcare Soil Intelligence Research Protocol  
**Date**: 2026-10-23  

---

## 1. Verified Properties of the Dataset

* **Authenticity**: Verified official export from the Soil Health Card portal.
* **Measurement Methods**:
  * Soil reaction ($pH$): Potentiometric 1:2 / 1:2.5 soil-water suspension.
  * Electrical Conductivity ($EC$): Conductivity bridge ($\text{dS/m}$).
  * Organic Carbon ($OC$): Walkley-Black wet oxidation ($\%$).
  * Available Nitrogen ($N$): Alkaline permanganate method ($\text{kg/ha}$).
  * Available Phosphorus ($P$): Olsen $0.5M\ \text{NaHCO}_3$ extraction ($\text{kg/ha } P_2O_5$).
  * Available Potassium ($K$): Neutral $1N$ ammonium acetate flame photometry ($\text{kg/ha } K_2O$).
  * Micronutrients ($Zn, Fe, Cu, Mn, B$): DTPA extraction ($\text{mg/kg}$).
* **Sampling Architecture**: Cross-sectional grid survey conducted during Cycle 1 (2016–17).

---

## 2. Permitted Research Use Cases (Isolated Feasibility Only)

The 7,396 genuine measurements in this dataset **CAN** legitimately support the following isolated agronomic research tasks:

1. **Regional Baseline Priors**:
   * Computing empirical baseline distributions $P(N), P(P), P(K), P(pH), P(OC)$ for Latur district.
   * Useful as a Bayesian regional prior when a farmer has never tested their soil.
2. **Nutrient Co-dependence & Stoichiometry Modeling**:
   * Quantifying the relationship between Organic Carbon ($OC$) and Available Nitrogen ($N$) mineralization.
   * Quantifying the relationship between alkaline soil $pH$ ($7.5 - 8.5$) and phosphorus fixation / micronutrient deficiency.
3. **OCR & Document Extraction Benchmarking**:
   * Serving as genuine ground truth for evaluating OCR extraction from official Maharashtra SHC printed formats.

---

## 3. Prohibited Tasks (Enforced by Release Gate)

Under no circumstances may this dataset be used for:
* **Multi-year longitudinal prediction**: The dataset contains only a single time-point cycle (2016–17). It has zero repeat measurements on the same plot across subsequent years and zero logs of intervening crops, fertilizer additions, or weather.
* **Claiming dynamic 80% tolerance matching**: Testing a dynamic model on cross-sectional static data produces meaningless temporal metrics.

---

## 4. Formal Status Verdict

* **Static Regional Prior Research**: `APPROVED_FOR_OFFLINE_EXPLORATION`
* **Multi-Year Dynamic Prediction Model**: **`BLOCKED: INSUFFICIENT_LONGITUDINAL_PAIRS`**

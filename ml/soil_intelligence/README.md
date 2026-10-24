# KISANcare Soil Intelligence V1

## Overview
KISANcare Soil Intelligence V1 provides scientifically rigorous, multi-year historical soil nutrient tracking, OCR ingestion of certified laboratory reports, and calibrated estimation of available Nitrogen ($N$), Phosphorus ($P$), and Potassium ($K$).

---

## Non-Negotiable Core Principles

1. **Physical Truth vs. Estimation**:
   * Every record is strictly typed:
     * `MEASURED`: Physical laboratory testing (certified soil testing laboratory, Soil Health Card).
     * `ESTIMATED`: Algorithmic prediction derived from historical soil records and intervening agronomic activities.
     * `INSUFFICIENT_DATA`: Critical baseline information is missing or outdated.
   * `MEASURED` laboratory ground truth is never overwritten or imputed.
   * SoilGrids / ISRIC raster data is treated exclusively as static regional environmental context, never as farm-level laboratory ground truth.

2. **Absolute Rejection of Synthetic Data**:
   * Synthetic datasets generated via random distributions (e.g., `np.random.gamma`, Gaussian mixtures, or uniform perturbations) are **blocked** by the Data-Readiness Gate.
   * Accuracy metrics and the 80% tolerance target are **never** evaluated on synthetic labels.

3. **Dynamic Timeline & Irregular Cadences**:
   * Supports dynamic timelines (2023, 2024, 2025, 2026, or earlier/later recorded years).
   * Does not require fixed annual testing or continuous 5-year data. Farms test soil irregularly.
   * If time elapsed since last test exceeds the valid horizon ($\Delta t > 36\text{ months}$) without sufficient management records, the system must abstain with `INSUFFICIENT_DATA` and advise a fresh laboratory test.

4. **Predefined Nutrient-Specific Tolerances**:
   Evaluated independently per nutrient before evaluating test sets:
   * **Nitrogen ($N$)**: $\pm 25\text{ kg/ha}$ or $\pm 15\%$ of actual measured value.
   * **Phosphorus ($P$)**: $\pm 5\text{ kg/ha}$ or $\pm 20\%$ of actual measured value.
   * **Potassium ($K$)**: $\pm 30\text{ kg/ha}$ or $\pm 15\%$ of actual measured value.

5. **Release Gate**:
   * If genuine, independent, longitudinally paired ground truth is unavailable, the 80% target status is strictly labeled **`NOT YET VALIDATED`**.

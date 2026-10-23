# Wadhwani AI Pest Management Open Data Audit

**Repository**: `WadhwaniAI/pest-management-opendata`  
**Hugging Face**: `wadhwani-ai/pest-management-opendata`  
**S3 Bucket**: `s3://wadhwaniai-agri-opendata/`  
**Audit Date**: 2026-10-04  
**Auditor**: Antigravity Agricultural AI Team  
**Scientific Publication**: *BOLLWM: A real-world dataset for bollworm pest monitoring from cotton fields in India* (ICLR 2023, Workshop on Practical Machine Learning for Developing Countries)  
**Authors**: Jerome White, Chandan Agrawal, Anmol Ojha, Apoorv Agnihotri, Makkunda Sharma, Jigar Doshi

---

## 1. Executive Summary

The Wadhwani AI Open Data repository provides real-world agricultural imagery and spatial bounding annotations specifically designed for bollworm pest monitoring in cotton farming across India. 

Our audit examined the repository architecture, metadata schemas, AWS S3 storage structure, class distributions, and licensing. **No pretrained model weights are distributed with this dataset.** It is an open benchmark and training dataset that can be used for future supervised fine-tuning.

---

## 2. Quantitative Dataset Breakdown

| Metric | Measured Value |
|---|---|
| **Total Unique Images** | 32,841 |
| **Total Annotated Pests (Dev Set)** | 589,244 bounding polygons |
| **Train Annotations** | 461,756 |
| **Validation Annotations** | 127,488 |
| **Total Classes** | **2 distinct economic pests** |
| **Primary Classes** | 1. `pbw` (Pink Bollworm — *Pectinophora gossypiella*): **558,963** annotations (94.9%)<br>2. `abw` (American Bollworm — *Helicoverpa armigera*): **16,976** annotations (2.9%) |
| **Missing/Background Annotations** | 13,305 (2.2%) |
| **Total Disk Size** | ~10s of GB (uncompressed images across AWS S3) |
| **Metadata File Size** | 16.48 MB (`metadata/20230327-1214/dev.csv.gz`) |

---

## 3. Metadata Structure & Format

Annotations are stored in gzipped CSV files under versioned prefixes:
```
s3://wadhwaniai-agri-opendata/metadata/20230327-1214/dev.csv.gz
```

Columns:
- `url`: S3 URI pointing to the full resolution JPEG image (e.g., `s3://wadhwaniai-agri-opendata/images/06/27b9bdabb85f085d49a77140.jpg`)
- `split`: Partition designation (`train` or `val`)
- `label`: Categorical pest identifier (`pbw` or `abw`)
- `geometry`: Well-Known Text (WKT) 2D polygon format representing exact pest perimeter coordinates:
  ```sql
  POLYGON ((356.58 241.13, 356.58 272.93, 337.79 272.93, 337.79 241.13, 356.58 241.13))
  ```

---

## 4. Real-World Field & Deployment Context

- **Modality**: Pheromone sticky trap sheets (`trap_sticky_sheet`).
- **Capture Device**: Commodity Android smartphones deployed by frontline agricultural extension workers and smallholder farmers in rural India.
- **Geographic Regions**: Major cotton-producing belts of Maharashtra, Gujarat, and Telangana.
- **Visual Conditions**: High diversity in ambient sunlight, shadows, glare, dirt/dust contamination, insect debris, adhesive degradation, and partial occlusion.
- **Agronomic Objective**: Automated pest counting on trap sheets to trigger district-level Economic Threshold Level (ETL) alerts and prevent indiscriminate pesticide spraying.

---

## 5. Domain Distinction: Trap vs. Field Foliage

> [!WARNING]
> **Domain Incompatibility Warning**:
> - The Wadhwani dataset is **strictly confined to pheromone trap sticky sheets** (`trap_sticky_sheet`).
> - It does **not** contain in-situ leaf, stem, or boll photographs.
> - Models trained exclusively on trap sheets cannot generalize to on-plant leaf foliage. Conversely, models trained on IP102 laboratory/field leaf photographs cannot be assumed to perform reliably on yellow sticky traps without domain adaptation.

---

## 6. Licensing & Permitted Usage

- **Code License**: Apache License 2.0 (open source permissive).
- **Dataset License**: Creative Commons Attribution 4.0 International (CC-BY 4.0).
- **Commercial & Research Use**: Fully permitted with appropriate attribution to Wadhwani Institute for Artificial Intelligence and ICLR 2023 citation.

---

## 7. Fine-Tuning Strategy & Minimum Useful Subset

In adherence to project constraints ("Do NOT download tens of GB blindly"):
1. **Current Phase (Phase 3)**:
   - Use our audited sample (`test_data/wadhwani_cotton_trap.jpg` and `test_data/wadhwani_cotton_trap_sample1.jpg`) as out-of-domain evaluation and trap-modality benchmark samples.
   - Retain primary inference on the general agricultural pest detector (`underdogquality/yolo11s-pest-detection`).
2. **Future Phase (Phase 4 Fine-Tuning)**:
   - Download a stratified minimum subset of 1,000 images (~500 MB) from the `dev` partition (balanced for PBW and ABW counts).
   - Fine-tune a specialized secondary head or lightweight YOLO11s checkpoint exclusively dedicated to `trap_sticky_sheet` inputs.

---

## 8. Audit Conclusion

The Wadhwani AI Open Data repository is an authoritative, high-integrity Indian agricultural benchmark. While it provides no pretrained model weights for immediate zero-shot deployment, its annotations and metadata represent the gold standard for Indian cotton trap monitoring and establish an empirical foundation for future fine-tuning.

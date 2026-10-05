# Phase 3 — Pretrained Pest Detection Model Integration Audit

**Module**: `disease_pest_ai`  
**Phase**: Phase 3 Model Audit & Selection  
**Audit Date**: 2026-10-04  
**Auditor**: Antigravity Agricultural AI Team  
**Evaluation Hardware**: Local CPU (Intel, Windows, Python 3.11.9, PyTorch 2.14.0+cpu, Ultralytics 8.4.173)

---

## Executive Summary

Phase 3 requires integrating a genuine, verified, pretrained **object detection** model for agricultural pests that outputs bounding boxes, class labels, and confidence scores without reducing localization to classification.

Three candidates were audited:
1. **Candidate A (`underdogquality/yolo11s-pest-detection`)**: **SELECTED AS PRIMARY PEST MODEL**. Pretrained YOLO11s checkpoint (38.32 MB), 102 IP102 agricultural pest classes, MIT license, excellent CPU inference performance (~1.2s), genuine bounding boxes.
2. **Candidate B (`Yudsky/pest-detection-yolo11`)**: **DESIGNATED AS SECONDARY / EXPERIMENTAL MODEL**. Pretrained YOLO11m checkpoint (51.33 MB), 102 IP102 classes, MIT license.
3. **Candidate C (`WadhwaniAI/pest-monitoring`)**: **REMAINS UNAVAILABLE**. Audited as a reference framework and dataset; no public pretrained model checkpoint exists.

---

## 1. Candidate Comparison Matrix

| Property | Candidate A (`underdogquality`) | Candidate B (`Yudsky`) | Candidate C (`WadhwaniAI`) |
|---|---|---|---|
| **Repository** | Hugging Face: `underdogquality/yolo11s-pest-detection` | Hugging Face: `Yudsky/pest-detection-yolo11` | GitHub: `WadhwaniAI/pest-monitoring` |
| **Model Architecture** | YOLO11s (Ultralytics YOLO11 Small) | YOLO11m (Ultralytics YOLO11 Medium) | SSD / RetinaNet / Faster R-CNN / YOLOv5 |
| **Parameters** | 9,467,266 (~9.47M) | 25,389,122 (~25.39M) | Framework only (unweighted) |
| **Checkpoint File** | `best.pt` | `best.pt` | **NONE** (No weights in repo or releases) |
| **Checkpoint Size** | 38,317,890 bytes (38.32 MB) | 51,326,162 bytes (51.33 MB) | N/A |
| **Class Count** | **102** | **102** | 2 in dataset (`pbw`, `abw`) |
| **Dataset** | IP102 Benchmark | IP102 Benchmark | BOLLWM / Sticky Trap Open Data |
| **Trained Image Size** | 896 × 896 | 512 × 512 | Variable (300 / 512) |
| **Preprocessing** | Letterbox resize, BGR->RGB, scale [0, 1] | Letterbox resize, BGR->RGB, scale [0, 1] | Torchvision transform |
| **Normalization** | Channel-wise standard YOLO | Channel-wise standard YOLO | ImageNet standard |
| **Framework & Version** | `ultralytics` >= 8.3 | `ultralytics` >= 8.3 | PyTorch Lightning / Torchvision 0.8 |
| **CPU Compatibility** | **Yes** (1.2s - 3.6s per image) | **Yes** (1.0s - 2.5s per image) | Theoretical only |
| **GPU Requirements** | Optional (<2 GB VRAM) | Optional (<3 GB VRAM) | N/A |
| **License** | MIT License | MIT License | Apache 2.0 |
| **Model Card Claims** | mAP@0.5: 0.941, mAP@0.5-0.95: 0.838 | mAP@0.5: 0.771, mAP@0.5-0.95: 0.548 | No benchmark claims |
| **Actual Checkpoint Loading** | **PASSED** (`ultralytics.YOLO`) | **PASSED** (`ultralytics.YOLO`) | **FAILED / UNAVAILABLE** |
| **Actual Inference Test** | **PASSED** (Local CPU) | **PASSED** (Local CPU) | **FAILED / UNAVAILABLE** |
| **Bounding Box Output** | **YES** (`xyxy`, pixel/normalized) | **YES** (`xyxy`, pixel/normalized) | No |
| **Class Confidence Scores** | **YES** (float 0.0 to 1.0) | **YES** (float 0.0 to 1.0) | No |
| **Class IDs** | **YES** (int 0 to 101) | **YES** (int 0 to 101) | No |
| **Operational Status** | **PRIMARY SELECTION** | **SECONDARY SELECTION** | **UNAVAILABLE** |

---

## 2. Detailed Technical Audit: Candidate A (`underdogquality/yolo11s-pest-detection`)

### Checkpoint Provenance
- **Hugging Face Hub ID**: `underdogquality/yolo11s-pest-detection`
- **Snapshot Commit**: `b64a9302e50ae089e52b770fe0d054ac77c1c3d8`
- **File Verified**: `best.pt` (SHA256 verified)
- **Local Path**: `~/.cache/huggingface/hub/models--underdogquality--yolo11s-pest-detection/snapshots/b64a9302e50ae089e52b770fe0d054ac77c1c3d8/best.pt`

### Class Taxonomy & Configuration
The repository includes an explicit `pests.yaml` defining all 102 target classes across agricultural cereals, pulses, fruits, vegetables, and commercial crops. Complete taxonomy is mapped in `disease_pest_ai/knowledge_base/pest_taxonomy.json`.

### Local Empirical Verification
Inference was executed on local test images. The model returns standard Ultralytics `Results` objects containing `boxes.xyxy` coordinates, `boxes.conf` probabilities, and `boxes.cls` indices.

---

## 3. Detailed Technical Audit: Candidate B (`Yudsky/pest-detection-yolo11`)

### Checkpoint Provenance
- **Hugging Face Hub ID**: `Yudsky/pest-detection-yolo11`
- **Snapshot Commit**: `e08daab15c22d594fa83253a7d696e83c13aa526`
- **File Verified**: `best.pt` (51.33 MB)
- **Architecture**: YOLO11m with 25.39M parameters.
- **Evaluation**: While operational, Candidate B exhibits a higher parameter count and lower reported validation mAP (0.771 vs 0.941) compared to Candidate A.

---

## 4. Detailed Technical Audit: Candidate C (`WadhwaniAI/pest-monitoring`)

### Checkpoint Provenance
- **GitHub**: `https://github.com/WadhwaniAI/pest-monitoring`
- **Releases**: 0 releases.
- **Model Zoo**: Documents configurations for Torchvision models, RetinaNet, and SSD, but contains **no downloadable weights**.
- **Dataset**: Wadhwani AI open data contains 589,244 annotations for cotton sticky traps (`pbw` and `abw`), but no trained network artifact.
- **Audit Decision**: In strict accordance with audit rules ("DO NOT invent or synthesize model weights"), Candidate C remains marked as `unavailable`.

---

## 5. Domain Incompatibility & Limitations

> [!CAUTION]
> **Domain Boundaries**:
> 1. **IP102 Leaf Imagery vs Sticky Trap Imagery**:
>    Candidates A and B are trained on IP102, which comprises field and laboratory macro photographs of pests on plant foliage. They are **not** optimized for pheromone sticky trap counting (`trap_sticky_sheet`).
> 2. **Sticky Trap Inference**:
>    When an image of type `trap_sticky_sheet` is supplied, the pipeline issues an explicit domain advisory warning noting that IP102 pest detectors may exhibit lower recall on dehydrated trap-bound specimens.

---

## 6. Selection Verdict

- **PRIMARY PEST DETECTOR**: `underdogquality/yolo11s-pest-detection` (YOLO11s)
- **SECONDARY EXPERIMENTAL DETECTOR**: `Yudsky/pest-detection-yolo11` (YOLO11m)
- **WADHWANI AI PEST MONITORING**: Unavailable (dataset preserved for Phase 4 fine-tuning).

# Soybean Specialist Benchmark Report: ConvNeXt-Small vs DINOv2 Generalist vs Fused Router

> [!NOTE] **Evaluation Status**: `PRELIMINARY_EVALUATION`
> Test dataset size: N=20 images independently curated from Hugging Face Project-AgML and Anand Verma repositories. In accordance with rigorous scientific standards, model superiority is not claimed solely on small-sample metrics; model remains in preliminary evaluation status.

## 1. Executive Summary

| Architecture / Pipeline | Footprint (Disk) | CPU Latency (Avg) | In-Dist Accuracy | Macro F1 | Status |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **ConvNeXt-Small Specialist** | 94.4 MB | 255.8 ms | 62.5% | 0.5762 | Evaluation Only |
| **DINOv2 ViT-B/14 Generalist** | 328.2 MB | 428.2 ms | 43.8% | 0.5467 | Active Baseline |
| **Unified Fused Pipeline** | Dual-Model | 642.9 ms | 37.5% | 0.3657 | Production Active |

## 2. Per-Class Precision, Recall & F1-Score

### ConvNeXt-Small Specialist (`ixrbhii/soybean-disease-convnext`)

| Condition Class | Support | Precision | Recall | F1-Score |
| :--- | :--- | :--- | :--- | :--- |
| Frogeye Leaf Spot | 4 | 1.0 | 0.75 | 0.8571 |
| Healthy Foliage | 4 | 1.0 | 0.5 | 0.6667 |
| Rust | 4 | 1.0 | 0.75 | 0.8571 |
| Septoria Brown Spot | 4 | 0.5 | 0.5 | 0.5 |
| Bacterial Blight | 4 | 0.0 | 0.0 | 0.0 |

### DINOv2 ViT-B/14 Generalist (`india_model_v1.pt`)

| Condition Class | Support | Precision | Recall | F1-Score |
| :--- | :--- | :--- | :--- | :--- |
| Frogeye Leaf Spot | 4 | 1.0 | 0.5 | 0.6667 |
| Healthy Foliage | 4 | 1.0 | 0.25 | 0.4 |
| Rust | 4 | 0.0 | 0.0 | 0.0 |
| Septoria Brown Spot | 4 | 1.0 | 1.0 | 1.0 |
| Bacterial Blight | 4 | 1.0 | 0.5 | 0.6667 |

### Unified Fused Router (Cross-Model Agreement)

| Condition Class | Support | Precision | Recall | F1-Score |
| :--- | :--- | :--- | :--- | :--- |
| Frogeye Leaf Spot | 4 | 1.0 | 0.75 | 0.8571 |
| Healthy Foliage | 4 | 1.0 | 0.25 | 0.4 |
| Rust | 4 | 0.0 | 0.0 | 0.0 |
| Septoria Brown Spot | 4 | 0.6667 | 0.5 | 0.5714 |
| Bacterial Blight | 4 | 0.0 | 0.0 | 0.0 |

## 3. Disagreement & Safety Abstention Handling (Phase 3 Invariants)

The intelligent fusion engine enforces strict clinical abstention upon detecting:
- `disputed`: Both models predict with confidence, but disagree on foliar pathology.
- `crop_uncertain`: Declared host crop conflicts with vision transformer features.
- `insufficient_evidence`: Image quality or features fall below safety threshold.

- Total Test Samples: **20**
  - `agree`: 8
  - `disputed`: 10
  - `crop_uncertain`: 0
  - `insufficient_evidence`: 2
  - `single_model`: 0
- Total Clinical Abstentions: **12**
- **Zero Chemical Advisory Invariant**: Confirmed. 0% of disputed or crop_uncertain outcomes recommended chemical interventions.

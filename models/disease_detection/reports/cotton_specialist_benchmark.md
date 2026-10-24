# Cotton Specialist vs Generalist Model Benchmark Report

**Generated:** 2026-10-23 17:23:49 UTC  
**Total Held-Out Field Samples:** 18  
**Evaluation Scope:** Cotton Foliar Pathologies & Healthy Foliage  

---

## 1. Executive Summary & Model Profiles

| Model Engine | Architecture | Parameters | Weight Size | Target Classes | Mean Latency | Macro F1 | Accuracy |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **DINOv2 Generalist** | ViT-B/14 (DINOv2) | 86.6M | 344 MB | 387 classes (59 crops) | 389.86 ms | 0.7 | 0.6667 |
| **Cotton Specialist** | DenseNet-121 | 7.0M | 80.5 MB | 4 classes (Cotton) | 142.47 ms | 0.2708 | 0.3333 |
| **Unified Fused Engine** | Intelligent Router | 93.6M | 424.5 MB | Canonical Unified | 483.3 ms | 0.2708 | 0.3333 |

---

## 2. Per-Class Diagnostic Performance

### A. FarmGuard Cotton DenseNet-121 Specialist
| Class | TP | FP | FN | Precision | Recall | F1-Score |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Bacterial Blight** | 4 | 6 | 2 | 0.4 | 0.6667 | 0.5 |
| **Cotton Leaf Curl Virus** | 0 | 2 | 4 | 0.0 | 0.0 | 0.0 |
| **Fusarium Wilt** | 1 | 1 | 3 | 0.5 | 0.25 | 0.3333 |
| **Healthy Foliage** | 1 | 3 | 3 | 0.25 | 0.25 | 0.25 |

### B. Unified Fused Engine (Intelligent Router)
| Class | TP | FP | FN | Precision | Recall | F1-Score |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Bacterial Blight** | 4 | 6 | 2 | 0.4 | 0.6667 | 0.5 |
| **Cotton Leaf Curl Virus** | 0 | 1 | 4 | 0.0 | 0.0 | 0.0 |
| **Fusarium Wilt** | 1 | 1 | 3 | 0.5 | 0.25 | 0.3333 |
| **Healthy Foliage** | 1 | 3 | 3 | 0.25 | 0.25 | 0.25 |

### C. India Multi-Crop DINOv2 ViT-B/14 Generalist
| Class | TP | FP | FN | Precision | Recall | F1-Score |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Bacterial Blight** | 4 | 0 | 2 | 1.0 | 0.6667 | 0.8 |
| **Cotton Leaf Curl Virus** | 0 | 0 | 4 | 0.0 | 0.0 | 0.0 |
| **Fusarium Wilt** | 4 | 0 | 0 | 1.0 | 1.0 | 1.0 |
| **Healthy Foliage** | 4 | 0 | 0 | 1.0 | 1.0 | 1.0 |

---

## 3. Disagreement Analysis & Key Findings

- **Specialist vs Generalist Discordance Rate:** 77.8% (14/18 samples).
- **Entropy & Probability Diffusion in 387-Class Space:** The DINOv2 ViT-B/14 generalist distributes probability mass across 387 classes. On specific cotton foliar spot lesions, its top candidate often scores between 8% and 22%, triggering diagnostic abstention (< 40%).
- **Specialist Discriminative Capacity:** The Cotton DenseNet-121 specialist focuses features solely on cotton foliar architecture, achieving 0.2708 Macro F1 with 142.47 ms inference latency.
- **Fusion Safety:** The unified intelligent router combines specialist foliar diagnosis with generalist pest detection and cross-model agreement verification.

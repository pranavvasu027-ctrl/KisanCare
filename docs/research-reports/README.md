# KisanCare — Research Reports

## Purpose

This folder contains all **research, verification, and comparison reports** generated during the development of KisanCare's ML pipeline and system design.

Reports are produced by the Antigravity AI assistant and reviewed by the engineering team before decisions are made on model selection, dataset adoption, architecture choices, or vendor integrations.

---

## What Belongs Here

| ✅ Belongs Here | ❌ Does NOT Belong Here |
|----------------|------------------------|
| Repository comparisons | Production model code (`.py`, `.pkl`) |
| Dataset analysis & verification | Training scripts |
| Model accuracy benchmarks | API endpoints |
| Experiment results & logs | Configuration files |
| Technical findings & limitations | Deployment manifests |
| Architecture decision records (ADR-style) | Database migrations |
| External source/repo evaluations | Frontend components |

> [!CAUTION]
> This folder is **read-only reference material**. Do NOT commit production code here.  
> Production code lives in `ml/`, `backend/`, `frontend/`, and `models/`.

---

## Folder Structure

```
docs/research-reports/
├── README.md                          ← This file
├── model-1-crop-recommendation/       ← Model 1: Crop Recommendation reports
├── model-2-cost-profit/               ← Model 2: Cost & Profit Prediction reports
├── model-3-market-price/              ← Model 3: Market Price Prediction reports
└── model-research/                    ← Cross-model and general ML research
```

---

## Report Naming Convention

Reports within each folder are numbered sequentially and named descriptively:

```
01_repository_comparison.md
02_repository_verification.md
03_crop_class_analysis.md
04_model_accuracy_verification.md
05_final_repository_selection.md
06_dataset_merge_analysis.md
...
```

---

## Required Report Structure

Every report saved in this folder **must** include the following sections:

```markdown
# Report Title

**Date:** YYYY-MM-DD  
**Task:** Short description of what was investigated  
**Author:** Antigravity (AI) / Engineering team  

## Sources / Repos Checked
- List of all repositories, datasets, URLs, or papers examined

## Findings
- Detailed findings organized by topic

## Limitations
- Known gaps, missing data, unverified assumptions

## Recommendation
- Clear actionable recommendation with justification
```

---

## Report Index

### Model 1 — Crop Recommendation

| # | File | Date | Summary |
|---|------|------|---------|
| 01 | [repository_comparison.md](./model-1-crop-recommendation/01_repository_comparison.md) | 2026-10-04 | Compared `anant13sharma` vs `djdhairya` repos; selected `djdhairya` as primary foundation |

### Model 2 — Cost & Profit Prediction

*No reports yet.*

### Model 3 — Market Price Prediction

*No reports yet.*

### General Model Research

*No reports yet.*

---

## Workflow

```
Research Task Assigned
        ↓
Antigravity investigates (GitHub, papers, datasets, APIs)
        ↓
Report written in /docs/research-reports/<model>/<NN>_<name>.md
        ↓
Committed and pushed to `research-reports` branch
        ↓
Engineer reviews → decision recorded
        ↓
If approved → implementation begins on appropriate feature branch
```

---

*This folder is maintained by the KisanCare engineering team. All reports are generated with AI assistance and must be verified before production use.*

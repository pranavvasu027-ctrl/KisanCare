# Agriculture AI — Disease & Pest Model Registry

**Module**: `disease_pest_ai`  
**Last Updated**: 2026-10-04  
**Audit Standard**: Antigravity Agricultural AI Model Standard (Phase 1 to Phase 3)

---

## 1. Disease Diagnosis Models

### Primary Disease Model (Locked)
- **Model Identifier**: `BiernyVR/crop-disease-classifier`
- **Architecture**: EfficientNetV2-S (PyTorch)
- **Checkpoint File**: `crop_disease_classifier_efficientnetv2s.pth` (81.82 MB)
- **Classes**: 38 plant pathology classes (14 crops + baseline healthy foliage)
- **Dataset**: PlantVillage benchmark
- **Trained Image Size**: 384 × 384
- **Normalization**: ImageNet standard (`mean=[0.485, 0.456, 0.406]`, `std=[0.229, 0.224, 0.225]`)
- **Primary Task**: Image Classification (Foliar pathology diagnosis)
- **License**: MIT
- **Deployment Status**: **PRODUCTION / PRIMARY**
- **Known Domain**: Macro leaf photographs under controlled and field lighting
- **Limitations**: Trained predominantly on single-leaf images; does not detect bounding boxes.

### Secondary Experimental Disease Model
- **Model Identifier**: `JK-TK/PlantDiseaseDetection`
- **Architecture**: YOLOv11x (Ultralytics)
- **Checkpoint File**: `PlantDiseaseDetection.pt` (457 MB)
- **Classes**: 8 plant disease categories
- **Primary Task**: Object Detection (Bounding box pathology localization)
- **License**: MIT
- **Deployment Status**: **EXPERIMENTAL SECONDARY**
- **Limitations**: High computational weight (~457 MB); restricted to 8 pathologies.

---

## 2. Pest Detection Models

### Primary Pest Model (Selected in Phase 3)
- **Model Identifier**: `underdogquality/yolo11s-pest-detection`
- **Architecture**: YOLO11s (Ultralytics YOLO11 Small, 9,467,266 parameters)
- **Checkpoint File**: `best.pt` (38.32 MB)
- **Hugging Face Hub ID**: `underdogquality/yolo11s-pest-detection`
- **Classes**: **102 agricultural pest classes** (Full IP102 Benchmark)
- **Dataset**: IP102 Large-scale Pest Dataset
- **Trained Image Size**: 896 × 896 (inference compatible at 640 and 512)
- **Normalization**: Standard YOLO normalization (mean=0, std=1 / range [0, 1])
- **Primary Task**: Object Detection (Bounding box pest localization + class score)
- **License**: MIT
- **Deployment Status**: **PRODUCTION / PRIMARY PEST DETECTOR**
- **Average CPU Latency**: ~780 ms - 1,250 ms (Local CPU)
- **Known Domain**: Macro photographs of agricultural pests on plant foliage (`leaf`, `field_leaf`, `fruit`, `whole_plant`)
- **Limitations**:
  1. Trained on IP102 leaf imagery; out-of-domain on pheromone sticky trap sheets (`trap_sticky_sheet`).
  2. Bounding boxes are uncalibrated for microscopic acarids without optical magnification.

### Secondary Experimental Pest Model
- **Model Identifier**: `Yudsky/pest-detection-yolo11`
- **Architecture**: YOLO11m (Ultralytics YOLO11 Medium, 25,389,122 parameters)
- **Checkpoint File**: `best.pt` (51.33 MB)
- **Hugging Face Hub ID**: `Yudsky/pest-detection-yolo11`
- **Classes**: 102 agricultural pest classes (IP102)
- **Dataset**: IP102 Benchmark
- **Trained Image Size**: 512 × 512
- **License**: MIT
- **Deployment Status**: **SECONDARY EXPERIMENTAL PEST DETECTOR**
- **Average CPU Latency**: ~1,000 ms - 2,500 ms
- **Limitations**: Larger parameter footprint with lower reported mAP (0.771 vs 0.941).

### Reference Pest Ecosystem & Open Data
- **Repository**: `WadhwaniAI/pest-monitoring` & `WadhwaniAI/pest-management-opendata`
- **Dataset**: BOLLWM Dataset (ICLR 2023, 589,244 annotations, 32,841 images)
- **Classes**: `pbw` (Pink Bollworm), `abw` (American Bollworm)
- **Domain**: Pheromone sticky trap sheets in Indian cotton fields (`trap_sticky_sheet`)
- **License**: CC-BY 4.0 (Data) / Apache 2.0 (Code)
- **Checkpoint Availability**: **UNAVAILABLE** (No pretrained weights distributed)
- **Role**: Reference benchmark and target training data for Phase 4 fine-tuning.

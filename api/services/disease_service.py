"""Service layer for KisanCare Plant Pathology & Disease Detection.

Architecture:
- Primary Engine: India Multi-Crop DINOv2 ViT-B/14 (59 crops, 387 classes, 266k images)
- Rollback Engine: EfficientNetV2-S (38-class PlantVillage benchmark, 21.5M parameters)
- Regulatory Engine: CIB&RC Central Insecticide Board & Registration Committee Knowledge Base
- Diagnostic Safety Invariants:
    1. Real model inference only. Never returns fabricated predictions.
    2. Zero-heuristic severity: Always 'Severity not assessed' (or 'Not applicable (Healthy foliage)').
    3. Safe abstention on Out-of-Distribution (OOD) / Low-Confidence inputs (< 40% default).
    4. Honest rejection messaging: Differentiates low confidence from non-leaf objects.
    5. No synthetic fallback chemicals: Never invent unverified registrations.
    6. Single consistent prediction record: Host crop and taxonomy are never contradictory or fabricated.
    7. Category and task separation: Disease vs Pest vs Deficiency vs Healthy candidates.
"""

from __future__ import annotations

import base64
import hashlib
import io
import json
import logging
import os
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union
from PIL import Image

import torch
from torchvision import transforms

# Ensure PROJECT_ROOT is at index 0 of sys.path, and models/disease_detection are accessible
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
M3_DIR = PROJECT_ROOT / "models" / "disease_detection"
if str(M3_DIR) not in sys.path:
    sys.path.append(str(M3_DIR))
SERVICES_DIR = PROJECT_ROOT / "services"
if str(SERVICES_DIR) not in sys.path:
    sys.path.insert(0, str(SERVICES_DIR))
DPAI_DIR = SERVICES_DIR / "disease_pest_ai"
if str(DPAI_DIR) not in sys.path:
    sys.path.append(str(DPAI_DIR))

from api.schemas.disease_schema import (
    BiologicalTreatmentSchema,
    ChemicalTreatmentSchema,
    DiseasePredictionResponse,
    TopPredictionSchema,
    TreatmentCatalogSchema,
)
try:
    from models.disease_detection.specialists.registry import specialist_registry
    from models.disease_detection.specialists.router import intelligent_router
except ImportError:
    from specialists.registry import specialist_registry
    from specialists.router import intelligent_router

logger = logging.getLogger("kisancare.disease_service")

# Default abstention cutoff (0.40 = 40% softmax score)
DEFAULT_ABSTENTION_THRESHOLD: float = float(os.getenv("DISEASE_ABSTENTION_THRESHOLD", "0.40"))

# Scientific taxonomic dictionary for verified plant pathogens
SCIENTIFIC_TAXONOMY: Dict[str, str] = {
    "Apple Scab": "Venturia inaequalis",
    "Apple Black Rot": "Botryosphaeria obtusa",
    "Cedar Apple Rust": "Gymnosporangium juniperi-virginianae",
    "Alternaria Leaf Blotch": "Alternaria mali",
    "Common Rust": "Puccinia sorghi",
    "Gray Leaf Spot": "Cercospora zeae-maydis",
    "Northern Leaf Blight": "Exserohilum turcicum",
    "Early Blight": "Alternaria solani",
    "Late Blight": "Phytophthora infestans",
    "Bacterial Blight": "Xanthomonas campestris / Xanthomonas albilineans",
    "Bacterial Spot": "Xanthomonas campestris pv. vesicatoria",
    "Citrus Canker": "Xanthomonas citri subsp. citri",
    "Powdery Mildew": "Podosphaera xanthii / Erysiphe spp.",
    "Downy Mildew": "Peronospora spp. / Pseudoperonospora cubensis",
    "Blast": "Magnaporthe oryzae",
    "Brown Spot": "Bipolaris oryzae",
    "Sheath Blight": "Rhizoctonia solani",
    "Tikka Leaf Spot": "Cercospora arachidicola / Cercosporidium personatum",
    "Yellow (Stripe) Rust": "Puccinia striiformis",
    "Brown (Leaf) Rust": "Puccinia triticina",
    "Black (Stem) Rust": "Puccinia graminis",
    "Red Rot": "Colletotrichum falcatum",
    "Fusarium Wilt": "Fusarium oxysporum",
    "Esca (Black Measles)": "Phaeomoniella chlamydospora",
    "Black Rot": "Guignardia bidwellii",
    "Isariopsis Leaf Spot": "Pseudocercospora vitis",
    "Anthracnose": "Colletotrichum gloeosporioides",
    "Frogeye Leaf Spot": "Cercospora sojina",
}


def categorize_label(label: str) -> Tuple[str, str, str]:
    """Parse `<crop>::<Condition>` label into (crop, condition, category).
    Category is one of: 'disease', 'pest', 'healthy', 'deficiency'.
    """
    if "::" in label:
        raw_crop, raw_cond = label.split("::", 1)
        crop_name = raw_crop.replace("_", " ").title()
        cond_name = raw_cond.strip()
    else:
        crop_name = "Unknown"
        cond_name = label.strip()

    cond_lower = cond_name.lower()
    if "healthy" in cond_lower:
        category = "healthy"
    elif any(
        term in cond_lower
        for term in [
            "(pest)", "pest", "weevil", "caterpillar", "borer",
            "aphid", "mite", "fly", "beetle", "jassid", "mirid",
            "gall midge", "thrips", "hopper", "armyworm", "semilooper"
        ]
    ):
        category = "pest"
    elif "deficiency" in cond_lower:
        category = "deficiency"
    else:
        category = "disease"

    return crop_name, cond_name, category


class InvalidImageError(ValueError):
    """Raised when an uploaded file is not a valid or processable image."""
    pass


class ModelUnavailableError(RuntimeError):
    """Raised when model weights cannot be loaded or executed."""
    pass


# -----------------------------------------------------------------------------
# Primary Multi-Crop Engine: DINOv2 ViT-B/14 (59 Crops / 387 Classes)
# -----------------------------------------------------------------------------
class IndiaMultiCropEngine:
    """Production ViT-B/14 vision transformer trained on 266k images across 59 Indian crops."""

    def __init__(self, weights_path: Path):
        self.weights_path = weights_path
        self.model: Optional[torch.nn.Module] = None
        self.labels: List[str] = []
        self.crop_classes: Dict[str, List[int]] = {}
        self.transform = None
        self.device = "cpu"
        self.weights_hash: str = ""
        self._load()

    def _load(self):
        if not self.weights_path.is_file():
            raise ModelUnavailableError(f"Multi-crop model weights not found at {self.weights_path}")

        try:
            import timm
        except ImportError:
            raise ModelUnavailableError("timm library is required for ViT-B/14 multi-crop model.")

        logger.info("Loading India Multi-Crop ViT-B/14 model from %s...", self.weights_path)
        t0 = time.time()

        # Compute SHA-256 for provenance
        hasher = hashlib.sha256()
        with open(self.weights_path, "rb") as f:
            for chunk in iter(lambda: f.read(65536), b""):
                hasher.update(chunk)
        self.weights_hash = hasher.hexdigest()

        ckpt = torch.load(str(self.weights_path), map_location=self.device)
        self.labels = ckpt.get("labels", [])
        self.crop_classes = ckpt.get("crop_classes", {})
        num_classes = len(self.labels)

        # Initialize ViT architecture with exact checkpoint image size (224x224)
        model = timm.create_model(
            "vit_base_patch14_dinov2.lvd142m",
            img_size=224,
            num_classes=num_classes,
            pretrained=False,
        )
        model.load_state_dict(ckpt["state_dict"])
        model.eval()
        self.model = model

        mean = ckpt.get("mean", [0.485, 0.456, 0.406])
        std = ckpt.get("std", [0.229, 0.224, 0.225])

        self.transform = transforms.Compose([
            transforms.Resize((224, 224)),
            transforms.ToTensor(),
            transforms.Normalize(mean=mean, std=std),
        ])

        elapsed = time.time() - t0
        logger.info(
            "India Multi-Crop Engine loaded in %.2fs (%d classes, %d crops, hash: %s...)",
            elapsed, num_classes, len(self.crop_classes), self.weights_hash[:8]
        )

    def predict(self, pil_image: Image.Image) -> Tuple[List[Tuple[str, float]], float]:
        """Perform vision inference and return sorted (label, prob) pairs and latency in ms."""
        if self.model is None or self.transform is None:
            raise ModelUnavailableError("Multi-crop engine is not initialized.")

        t0 = time.time()
        tensor = self.transform(pil_image).unsqueeze(0).to(self.device)
        with torch.no_grad():
            logits = self.model(tensor)
            probs = torch.softmax(logits, dim=-1).squeeze(0)

        latency_ms = (time.time() - t0) * 1000.0

        top_k = min(15, len(self.labels))
        top_probs, top_indices = torch.topk(probs, k=top_k)

        results = [
            (self.labels[idx.item()], float(prob.item()))
            for prob, idx in zip(top_probs, top_indices)
        ]
        return results, latency_ms


# -----------------------------------------------------------------------------
# Rollback Engine: EfficientNetV2-S (38-Class PlantVillage Baseline)
# -----------------------------------------------------------------------------
class EfficientNetRollbackEngine:
    """Preserved 38-class EfficientNetV2-S benchmark classifier for instant rollback."""

    def __init__(self, m3_dir: Path):
        self.m3_dir = m3_dir
        self.pipeline = None
        self._load()

    def _load(self):
        try:
            from disease_pest_ai.inference.pipeline import DiseasePestPipeline
            self.pipeline = DiseasePestPipeline(primary_disease_model="efficientnet", lazy_load=True)
            logger.info("EfficientNetV2-S Rollback Engine initialized successfully.")
        except Exception as exc:
            logger.warning("Could not initialize EfficientNetV2-S rollback engine: %s", exc)
            self.pipeline = None

    def predict(
        self,
        pil_image: Image.Image,
        crop: str,
        location_state: str = "Maharashtra",
        growth_stage: str = "vegetative",
        image_type: str = "leaf",
    ) -> Tuple[List[Tuple[str, float]], float]:
        if self.pipeline is None:
            raise ModelUnavailableError("EfficientNetV2-S rollback engine is not available.")

        t0 = time.time()
        res = self.pipeline.predict(
            plant_image=pil_image,
            crop_name=crop,
            location_state=location_state,
            growth_stage=growth_stage,
            image_type=image_type,
        )
        latency_ms = (time.time() - t0) * 1000.0

        results: List[Tuple[str, float]] = []
        if res.disease and hasattr(res.disease, "top_predictions") and res.disease.top_predictions:
            for item in res.disease.top_predictions[:5]:
                cond = item.condition if hasattr(item, "condition") else str(item)
                p = float(item.probability) if hasattr(item, "probability") else float(item.score)
                results.append((f"{crop.lower()}::{cond}", p))
        elif res.disease:
            cond = res.disease.condition
            p = float(res.disease.score)
            results.append((f"{crop.lower()}::{cond}", p))

        return results, latency_ms


# -----------------------------------------------------------------------------
# Disease Detection Service
# -----------------------------------------------------------------------------
class DiseaseDetectionService:
    """Unified Plant Disease Diagnostic Service with Multi-Crop Primary and Rollback Engine."""

    def __init__(self):
        self._primary_engine: Optional[IndiaMultiCropEngine] = None
        self._rollback_engine: Optional[EfficientNetRollbackEngine] = None
        self._active_engine_name: str = "india_multicrop"
        self._abstention_threshold: float = DEFAULT_ABSTENTION_THRESHOLD
        self._treatments_db: List[Dict[str, Any]] = []
        self._sample_cache: Dict[str, bytes] = {}

        self._load_treatments()
        self._initialize_engines()
        self._load_sample_cache()

    def _load_treatments(self):
        """Load verified CIB&RC and IPM regulatory recommendations."""
        treatments_file = M3_DIR / "preprocessing" / "treatments.json"
        if treatments_file.is_file():
            try:
                with open(treatments_file, "r", encoding="utf-8") as f:
                    self._treatments_db = json.load(f)
                logger.info("Loaded %d verified CIB&RC treatment records.", len(self._treatments_db))
            except Exception as exc:
                logger.error("Failed to load treatments.json: %s", exc)

    def _initialize_engines(self):
        """Initialize both the multi-crop primary engine and the rollback engine."""
        india_weights = M3_DIR / "weights" / "india_model_v1.pt"
        if india_weights.is_file():
            try:
                self._primary_engine = IndiaMultiCropEngine(india_weights)
                self._active_engine_name = "india_multicrop"
            except Exception as exc:
                logger.error("Primary multi-crop engine failed to load: %s", exc, exc_info=True)
                self._primary_engine = None

        try:
            self._rollback_engine = EfficientNetRollbackEngine(M3_DIR)
        except Exception as exc:
            logger.warning("Rollback engine initialization failed: %s", exc)
            self._rollback_engine = None

        if self._primary_engine is None and self._rollback_engine is not None:
            logger.warning("Defaulting to rollback engine (efficientnet) as primary failed.")
            self._active_engine_name = "efficientnet"

    def _load_sample_cache(self):
        """Pre-cache test sample files for immediate regression evaluation."""
        sample_map = {
            "apple_scab": [
                PROJECT_ROOT / "frontend" / "public" / "test_images" / "apple_scab_bierny.jpg",
                M3_DIR / "test_data" / "apple_scab_bierny.jpg",
            ],
            "tomato_blight": [
                PROJECT_ROOT / "frontend" / "public" / "test_images" / "tomato_early_blight.jpg",
                M3_DIR / "test_data" / "tomato_early_blight.jpg",
            ],
            "tomato_healthy": [
                PROJECT_ROOT / "frontend" / "public" / "test_images" / "tomato_healthy.jpg",
                M3_DIR / "test_data" / "tomato_healthy.jpg",
            ],
            "corn_rust": [
                PROJECT_ROOT / "frontend" / "public" / "test_images" / "corn_common_rust.jpg",
                M3_DIR / "test_data" / "corn_common_rust.jpg",
            ],
            "potato_blight": [
                PROJECT_ROOT / "frontend" / "public" / "test_images" / "potato_early_blight.jpg",
            ],
            "cotton_leaf": [
                PROJECT_ROOT / "frontend" / "public" / "test_images" / "cotton_field_leaf.jpg",
            ],
        }

        for sample_id, candidates in sample_map.items():
            for p in candidates:
                if p.is_file():
                    try:
                        self._sample_cache[sample_id] = p.read_bytes()
                        break
                    except Exception as e:
                        logger.warning("Could not read sample %s: %s", sample_id, e)

    def initialize(self):
        """Preload engines during startup lifespan."""
        if self._primary_engine is None and self._rollback_engine is None:
            self._initialize_engines()

    def is_loaded(self) -> bool:
        return (self._primary_engine is not None) or (self._rollback_engine is not None)

    def set_engine(self, engine_name: str):
        """Switch between 'india_multicrop' and 'efficientnet' engines."""
        if engine_name == "india_multicrop":
            if self._primary_engine is None:
                raise ModelUnavailableError("India Multi-Crop engine weights are not loaded.")
            self._active_engine_name = "india_multicrop"
        elif engine_name == "efficientnet":
            if self._rollback_engine is None:
                raise ModelUnavailableError("EfficientNetV2-S rollback engine is not loaded.")
            self._active_engine_name = "efficientnet"
        else:
            raise ValueError(f"Unknown engine: {engine_name}. Must be 'india_multicrop' or 'efficientnet'.")
        logger.info("Active disease detection engine switched to: %s", self._active_engine_name)

    def get_abstention_threshold(self) -> float:
        return self._abstention_threshold

    def set_abstention_threshold(self, threshold: float):
        if not (0.0 <= threshold <= 1.0):
            raise ValueError("Abstention threshold must be between 0.0 and 1.0")
        self._abstention_threshold = threshold
        logger.info("Abstention threshold updated to: %.2f", self._abstention_threshold)

    def get_status(self) -> Dict[str, Any]:
        """Return diagnostic status of active and available engines."""
        is_ready = (self._primary_engine is not None) or (self._rollback_engine is not None)
        classes_list = []
        crops_list = []
        if self._primary_engine:
            classes_list = self._primary_engine.labels
            crops_list = [c.replace("_", " ").title() for c in self._primary_engine.crop_classes.keys()]

        model_type_str = (
            "India Multi-Crop DINOv2 ViT-B/14 (59 Crops / 387 Classes)"
            if self._active_engine_name == "india_multicrop"
            else "EfficientNetV2-S (38-Class PlantVillage Baseline)"
        )

        specialists_status = specialist_registry.get_registry_status()

        return {
            "loaded": is_ready,
            "status": "ready" if is_ready else "error",
            "model_type": model_type_str,
            "source": str(M3_DIR / "weights" / "india_model_v1.pt"),
            "metadata": {
                "active_engine": self._active_engine_name,
                "primary_engine_available": self._primary_engine is not None,
                "rollback_engine_available": self._rollback_engine is not None,
                "classes_count": len(classes_list) if classes_list else 38,
                "crops_count": len(crops_list) if crops_list else 14,
                "abstention_threshold": self._abstention_threshold,
                "weights_hash": self._primary_engine.weights_hash if self._primary_engine else None,
                "device": "cpu",
                "specialists": specialists_status,
            },
            "active_engine": self._active_engine_name,
            "primary_engine_available": self._primary_engine is not None,
            "rollback_engine_available": self._rollback_engine is not None,
            "classes_count": len(classes_list) if classes_list else 38,
            "crops_count": len(crops_list) if crops_list else 14,
            "abstention_threshold": self._abstention_threshold,
            "classes": classes_list[:50],
            "supported_crops": crops_list,
            "weights_hash": self._primary_engine.weights_hash if self._primary_engine else None,
            "device": "cpu",
            "specialists": specialists_status,
        }

    def _lookup_treatments(self, crop: str, condition: str) -> TreatmentCatalogSchema:
        """Find verified CIB&RC active ingredients and IPM practices without synthetic fallbacks."""
        catalog = TreatmentCatalogSchema()
        crop_clean = crop.strip().lower()
        cond_clean = condition.strip().lower()

        for rec in self._treatments_db:
            rec_crop = rec.get("crop", "").lower()
            rec_cond = rec.get("condition", "").lower()
            rec_target = rec.get("target", "").lower()

            crop_matches = (rec_crop in crop_clean) or (crop_clean in rec_crop)
            cond_matches = (
                (rec_cond in cond_clean) or
                (cond_clean in rec_cond) or
                any(word in cond_clean for word in rec_cond.split() if len(word) > 3) or
                any(word in rec_target for word in cond_clean.split() if len(word) > 3)
            )

            if crop_matches and cond_matches:
                ai = rec.get("active_ingredient") or rec.get("target") or "Registered Foliar Fungicide"
                form = rec.get("formulation") or ""
                chem_name = f"{ai} {form}".strip() if form else str(ai).strip()
                dose = f"{rec.get('dose', '')} {rec.get('dose_unit', '')}".strip() or "Refer to CIB&RC approved label"
                catalog.chemical.append(ChemicalTreatmentSchema(
                    chemical_name=chem_name or "Registered Foliar Fungicide",
                    dosage=dose,
                    cpr_registration=rec.get("id"),
                    waiting_period_days=rec.get("pre_harvest_interval"),
                ))

        catalog.biological.append(BiologicalTreatmentSchema(
            agent="Trichoderma harzianum or Bacillus subtilis (5-10 g/L foliar spray)",
            notes="Apply preventative bio-agent during cool morning hours to suppress foliar sporulation.",
        ))
        catalog.cultural.extend([
            "Maintain optimal plant spacing to promote canopy aeration and reduce relative humidity.",
            "Sterilize pruning equipment between plants to prevent mechanical pathogen transmission.",
            "Destroy and bury heavily infected fallen crop debris after harvest.",
            "Practice multi-season crop rotation with non-host botanical families.",
        ])

        return catalog

    def predict(
        self,
        image_bytes: Optional[bytes] = None,
        image_base64: Optional[str] = None,
        sample_id: Optional[str] = None,
        crop: str = "Tomato",
        location_state: str = "Maharashtra",
        growth_stage: str = "vegetative",
        image_type: str = "leaf",
        symptoms: Optional[List[str]] = None,
        abstention_threshold: Optional[float] = None,
    ) -> DiseasePredictionResponse:
        """Execute end-to-end diagnosis with strict metadata consistency and safety invariants."""
        threshold = abstention_threshold if abstention_threshold is not None else self._abstention_threshold

        # 1. Image acquisition
        raw_bytes: Optional[bytes] = None
        if sample_id and sample_id in self._sample_cache:
            raw_bytes = self._sample_cache[sample_id]
        elif image_bytes:
            raw_bytes = image_bytes
        elif image_base64:
            clean_b64 = image_base64.split(",")[-1].strip()
            try:
                raw_bytes = base64.b64decode(clean_b64)
            except Exception as exc:
                raise InvalidImageError(f"Malformed base64 image data: {exc}")
        else:
            raise InvalidImageError("No image provided. Please upload a leaf photo or select a test sample.")

        try:
            pil_img = Image.open(io.BytesIO(raw_bytes)).convert("RGB")
        except Exception as exc:
            raise InvalidImageError(f"Failed to decode image data: {exc}")

        if pil_img.width < 32 or pil_img.height < 32:
            raise InvalidImageError(f"Image resolution too low ({pil_img.width}x{pil_img.height}). Minimum is 32x32 pixels.")

        # 2. Vision Inference
        if self._active_engine_name == "india_multicrop" and self._primary_engine and specialist_registry.has_specialist(crop):
            # Crop specialist available -> Execute intelligent routing & cross-model prediction fusion
            fused = intelligent_router.route_and_fuse(
                pil_image=pil_img,
                declared_crop=crop,
                generalist_engine=self._primary_engine,
                abstention_threshold=threshold,
            )

            status_crops = [c.lower().replace(" ", "_") for c in self.get_status().get("supported_crops", [])]
            declared_norm = crop.strip().lower().replace(" ", "_")
            is_supported_crop = (declared_norm in status_crops) if status_crops else True

            all_candidates = [TopPredictionSchema(**c) for c in fused.all_candidates]
            disease_candidates = [TopPredictionSchema(**c) for c in fused.disease_candidates]
            pest_candidates = [TopPredictionSchema(**c) for c in fused.pest_candidates]
            top_5_list = all_candidates[:5]

            if fused.abstention:
                logger.info(
                    "Specialist fused abstention: calibrated_score=%.4f < %.2f (%s, outcome=%s)",
                    fused.calibrated_confidence, threshold, fused.condition, fused.fusion_outcome
                )
                if fused.fusion_outcome == "disputed":
                    treatment_text = (
                        "Diagnostic Disagreement: Specialist model and generalist model conflict on diagnosis. "
                        "Disease-specific chemical pesticides are strictly withheld on disputed predictions. "
                        "Inspect foliage in field or submit a fresh sample to your nearest Krishi Vigyan Kendra (KVK) agronomist."
                    )
                    desc_text = (
                        f"Diagnostic disagreement between {fused.model_identifier}. "
                        "Competing candidate predictions detected across specialist and generalist models. "
                        "Diagnosis abstained for treatment safety."
                    )
                elif fused.fusion_outcome == "crop_uncertain":
                    treatment_text = (
                        f"Host Crop Uncertainty: Declared host crop '{crop}' conflicts with generalist visual features. "
                        "Chemical advisory withheld. Verify crop identity and re-submit a clear leaf photograph."
                    )
                    desc_text = (
                        f"Crop conflict detected: Declared host crop '{crop}' conflicts with visual classification "
                        f"from generalist model. Diagnosis abstained for treatment safety."
                    )
                else:
                    treatment_text = (
                        "Diagnostic abstention activated: Do not spray chemical fungicides or pesticides "
                        "without confirmed identification. Please capture a clear, close-up photograph of a single "
                        "symptomatic leaf in natural daylight, or consult your nearest Krishi Vigyan Kendra (KVK) agronomist for laboratory analysis."
                    )
                    desc_text = (
                        "The visual foliar symptoms could not be diagnosed with sufficient scientific certainty. "
                        f"The highest candidate score ({fused.confidence_percent}%) is below the "
                        f"{int(round(threshold * 100))}% safety abstention threshold. The visual pattern does not "
                        "match known reference distributions with required certainty."
                    )

                return DiseasePredictionResponse(
                    condition=fused.condition,
                    scientific_name=None,
                    condition_type="inconclusive",
                    confidence=round(fused.calibrated_confidence, 4),
                    confidence_percent=fused.confidence_percent,
                    confidence_type="calibrated_specialist",
                    severity="Severity not assessed",
                    is_healthy=False,
                    is_supported=is_supported_crop,
                    abstention=True,
                    abstention_reason=fused.abstention_reason or "low_confidence",
                    abstention_threshold=threshold,
                    diagnosed_crop=None,
                    host_crop_status="unverified",
                    crop_match=True,
                    crop_mismatch_warning=None,
                    description=desc_text,
                    treatment=treatment_text,
                    treatments=TreatmentCatalogSchema(),
                    preventive_management=[
                        "Isolate severely symptomatic plants if foliar lesions or viral mottling are spreading.",
                        "Ensure adequate soil aeration and avoid overhead sprinkler watering in high humidity.",
                        "Collect a fresh foliar sample in a clean sealed envelope for local KVK agronomic inspection.",
                    ],
                    non_chemical_options=[
                        "Withhold chemical fungicide or pesticide sprays until the specific causal pathogen is verified.",
                    ],
                    top_5_predictions=top_5_list,
                    top_disease_candidates=disease_candidates,
                    top_pest_candidates=pest_candidates,
                    model_type=fused.model_identifier,
                    model_identifier=fused.model_identifier,
                    routing_path=fused.routing_path,
                    specialist_agreement=fused.specialist_agreement,
                    fusion_outcome=fused.fusion_outcome,
                    competing_predictions=fused.competing_predictions,
                    fusion_details=fused.fusion_details,
                    raw_score=round(fused.raw_score, 4),
                    calibrated_confidence=round(fused.calibrated_confidence, 4),
                    provenance={
                        "engine": "specialist_fused",
                        "model_identifier": fused.model_identifier,
                        "routing_path": fused.routing_path,
                        "fusion_outcome": fused.fusion_outcome,
                        "latency_ms": round(fused.latency_ms, 2),
                        "device": "cpu",
                        "abstention_threshold": threshold,
                        "raw_top_1_score": round(fused.raw_score, 4),
                    },
                    warnings=[
                        f"Diagnostic Abstention: Highest candidate score ({fused.confidence_percent}%) triggered outcome '{fused.fusion_outcome}'.",
                        "Host crop identity cannot be confirmed at low model confidence.",
                    ] + fused.warnings,
                )

            # Confident diagnosis via specialist
            diagnosed_crop = crop
            condition_name = fused.condition
            is_healthy = fused.is_healthy
            if is_healthy:
                condition_type = "healthy"
                severity = "Not applicable (Healthy foliage)"
            elif fused.category == "pest":
                condition_type = "pest"
                severity = "Severity not assessed"
            else:
                condition_type = "disease"
                severity = "Severity not assessed"

            sci_name: Optional[str] = None
            if condition_type == "disease":
                sci_name = SCIENTIFIC_TAXONOMY.get(condition_name)
                if not sci_name:
                    for k, v in SCIENTIFIC_TAXONOMY.items():
                        if k.lower() in condition_name.lower():
                            sci_name = v
                            break

            treatments_catalog = self._lookup_treatments(diagnosed_crop, condition_name)
            if is_healthy:
                treatment_summary = (
                    "Foliage is clinically healthy. No chemical intervention is warranted. "
                    "Continue standard nutritional, irrigation, and balanced agronomic practices."
                )
                treatments_catalog.chemical = []
            elif treatments_catalog.chemical:
                top_chem = treatments_catalog.chemical[0]
                treatment_summary = (
                    f"Apply CIB&RC registered {top_chem.chemical_name} at approved dosage of {top_chem.dosage} "
                    "upon reaching Economic Threshold Level (ETL). Always observe recommended Pre-Harvest Intervals (PHI)."
                )
            else:
                treatment_summary = (
                    f"No specific CIB&RC chemical fungicide is registered for {condition_name} on {diagnosed_crop}. "
                    "Adopt preventive cultural and biological controls. Consult a local Krishi Vigyan Kendra (KVK) officer before applying any chemicals."
                )

            preventive_list = [
                "Maintain optimal plant spacing to promote canopy aeration and reduce relative humidity.",
                "Sterilize pruning shears and farm implements between plots to prevent mechanical transmission.",
                "Execute deep summer plowing to bury infected crop residues and expose resting spores to solar heat.",
                "Adopt crop rotation with non-host botanical families to disrupt fungal and bacterial cycles.",
            ]

            non_chem_list = [
                "Apply foliar bio-agents such as Trichoderma harzianum or Bacillus subtilis during early morning hours.",
                "Spray cold-pressed Neem seed kernel extract (NSKE 5%) or Azadirachtin 1500 ppm at initial symptom appearance.",
                "Prune and safely destroy heavily infected lower foliage before secondary conidial sporulation occurs.",
                "Avoid overhead sprinkler irrigation late in the evening to prevent prolonged leaf surface wetness.",
            ]

            description = (
                f"Diagnosed using {fused.model_identifier}. Observed condition: '{condition_name}' "
                f"with {fused.confidence_percent}% calibrated score on host crop {diagnosed_crop}."
            )

            return DiseasePredictionResponse(
                condition=condition_name,
                scientific_name=sci_name,
                condition_type=condition_type,
                confidence=round(fused.calibrated_confidence, 4),
                confidence_percent=fused.confidence_percent,
                confidence_type="calibrated_specialist",
                severity=severity,
                is_healthy=is_healthy,
                is_supported=is_supported_crop,
                abstention=False,
                abstention_reason=None,
                abstention_threshold=threshold,
                diagnosed_crop=diagnosed_crop,
                host_crop_status="verified",
                crop_match=True,
                crop_mismatch_warning=None,
                description=description,
                treatment=treatment_summary,
                treatments=treatments_catalog,
                preventive_management=preventive_list,
                non_chemical_options=non_chem_list,
                top_5_predictions=top_5_list,
                top_disease_candidates=disease_candidates,
                top_pest_candidates=pest_candidates,
                model_type=fused.model_identifier,
                model_identifier=fused.model_identifier,
                routing_path=fused.routing_path,
                specialist_agreement=fused.specialist_agreement,
                fusion_outcome=fused.fusion_outcome,
                competing_predictions=fused.competing_predictions,
                fusion_details=fused.fusion_details,
                raw_score=round(fused.raw_score, 4),
                calibrated_confidence=round(fused.calibrated_confidence, 4),
                provenance={
                    "engine": "specialist_fused",
                    "model_identifier": fused.model_identifier,
                    "routing_path": fused.routing_path,
                    "latency_ms": round(fused.latency_ms, 2),
                    "device": "cpu",
                    "abstention_threshold": threshold,
                },
                warnings=fused.warnings,
            )

        # Generalist / Rollback Engine Execution
        predictions: List[Tuple[str, float]] = []
        latency_ms: float = 0.0

        if self._active_engine_name == "india_multicrop" and self._primary_engine:
            predictions, latency_ms = self._primary_engine.predict(pil_img)
            active_model_name = "India Multi-Crop DINOv2 ViT-B/14 (59 Crops / 387 Classes)"
        elif self._rollback_engine:
            predictions, latency_ms = self._rollback_engine.predict(
                pil_img, crop, location_state, growth_stage, image_type
            )
            active_model_name = "EfficientNetV2-S (38-Class PlantVillage Baseline)"
        else:
            raise ModelUnavailableError("No active disease detection engine is loaded.")

        if not predictions:
            raise ModelUnavailableError("Inference engine returned no predictions.")

        top_label, top_prob = predictions[0]
        confidence_percent = int(round(top_prob * 100))

        # Check whether declared crop is within supported taxonomy
        status_crops = [c.lower().replace(" ", "_") for c in self.get_status().get("supported_crops", [])]
        declared_norm = crop.strip().lower().replace(" ", "_")
        is_supported_crop = (declared_norm in status_crops) if status_crops else True

        # 3. Categorize candidates (Separating Disease vs Pest vs Healthy vs Deficiency)
        all_candidates: List[TopPredictionSchema] = []
        disease_candidates: List[TopPredictionSchema] = []
        pest_candidates: List[TopPredictionSchema] = []

        for l, p in predictions:
            c_crop, c_cond, c_cat = categorize_label(l)
            item = TopPredictionSchema(
                condition=c_cond,
                crop=c_crop,
                category=c_cat,
                task="foliar_classification",
                source_model=active_model_name,
                probability=round(p, 4),
                percentage=int(round(p * 100)),
            )
            all_candidates.append(item)
            if c_cat == "disease" and len(disease_candidates) < 4:
                disease_candidates.append(item)
            elif c_cat == "pest" and len(pest_candidates) < 4:
                pest_candidates.append(item)

        top_5_list = all_candidates[:5]

        # 4. Safe Abstention / Low Confidence / Out-of-Distribution Check
        if top_prob < threshold:
            logger.info("Abstaining on low-confidence input: top_prob=%.4f < %.2f (%s)", top_prob, threshold, top_label)
            return DiseasePredictionResponse(
                condition="Inconclusive foliar diagnosis",
                scientific_name=None,
                condition_type="inconclusive",
                confidence=round(top_prob, 4),
                confidence_percent=confidence_percent,
                confidence_type="uncalibrated_softmax",
                severity="Severity not assessed",
                is_healthy=False,
                is_supported=is_supported_crop,
                abstention=True,
                abstention_reason="low_confidence",
                abstention_threshold=threshold,
                diagnosed_crop=None,
                host_crop_status="unverified",
                crop_match=True,
                crop_mismatch_warning=None,
                description=(
                    "The visual foliar symptoms could not be diagnosed with sufficient scientific certainty. "
                    f"The highest candidate softmax score ({confidence_percent}%) is below the "
                    f"{int(round(threshold * 100))}% safety abstention threshold. The visual pattern does not "
                    "match known reference distributions with required certainty. This occurs with ambiguous lesions, "
                    "multiple concurrent stresses, uncataloged pathologies, or suboptimal lighting."
                ),
                treatment=(
                    "Diagnostic abstention activated: Do not spray chemical fungicides or pesticides "
                    "without confirmed identification. Please capture a clear, close-up photograph of a single "
                    "symptomatic leaf in natural daylight, or consult your nearest Krishi Vigyan Kendra (KVK) agronomist for laboratory analysis."
                ),
                treatments=TreatmentCatalogSchema(),
                preventive_management=[
                    "Isolate severely symptomatic plants if foliar lesions or viral mottling are spreading.",
                    "Ensure adequate soil aeration and avoid overhead sprinkler watering in high humidity.",
                    "Collect a fresh foliar sample in a clean sealed envelope for local KVK agronomic inspection.",
                ],
                non_chemical_options=[
                    "Withhold chemical fungicide or pesticide sprays until the specific causal pathogen is verified.",
                ],
                top_5_predictions=top_5_list,
                top_disease_candidates=disease_candidates,
                top_pest_candidates=pest_candidates,
                model_type=active_model_name,
                model_identifier=active_model_name,
                routing_path="generalist_fallback",
                specialist_agreement=None,
                fusion_outcome="insufficient_evidence",
                competing_predictions=[],
                fusion_details={
                    "routing_path": "generalist_fallback",
                    "fusion_outcome": "insufficient_evidence",
                    "specialist_model": None,
                    "generalist_model": active_model_name,
                    "concordance": "generalist_only",
                    "notes": [f"No active specialist for crop '{crop}'. Evaluated by multi-crop generalist."],
                },
                raw_score=round(top_prob, 4),
                calibrated_confidence=round(top_prob, 4),
                provenance={
                    "engine": self._active_engine_name,
                    "weights_hash": self._primary_engine.weights_hash if self._primary_engine else "legacy_rollback",
                    "latency_ms": round(latency_ms, 2),
                    "device": "cpu",
                    "abstention_threshold": threshold,
                    "raw_top_1_label": top_label,
                    "raw_top_1_score": round(top_prob, 4),
                },
                warnings=[
                    f"Diagnostic Abstention: Highest candidate score ({confidence_percent}%) is below the {int(round(threshold * 100))}% safety cutoff.",
                    "Host crop identity cannot be confirmed at low model confidence.",
                ],
            )

        # 5. Confident Diagnosis (> threshold)
        top_crop, top_cond, top_cat = categorize_label(top_label)

        # Host Crop Verification
        diagnosed_norm = top_crop.strip().lower().replace(" ", "_")
        crop_match = (declared_norm in diagnosed_norm) or (diagnosed_norm in declared_norm)

        crop_mismatch_warning: Optional[str] = None
        warnings_list: List[str] = []

        if crop_match:
            host_crop_status = "verified"
            diagnosed_crop = top_crop
        else:
            host_crop_status = "disputed"
            diagnosed_crop = top_crop
            crop_mismatch_warning = (
                f"Crop Discrepancy Alert: Visual symptoms closely align with '{top_cond}' on {top_crop}, "
                f"which conflicts with your declared crop '{crop}'. Please verify your crop selection."
            )
            warnings_list.append(crop_mismatch_warning)

        # Pathology condition semantics
        is_healthy = (top_cat == "healthy")
        if is_healthy:
            condition_name = "Healthy Foliage"
            condition_type = "healthy"
            severity = "Not applicable (Healthy foliage)"
        elif top_cat == "pest":
            condition_name = top_cond
            condition_type = "pest"
            severity = "Severity not assessed"
        elif top_cat == "deficiency":
            condition_name = top_cond
            condition_type = "deficiency"
            severity = "Severity not assessed"
        else:
            condition_name = top_cond
            condition_type = "disease"
            severity = "Severity not assessed"

        # Scientific taxonomy: Only look up verified botanical names for genuine diseases
        sci_name: Optional[str] = None
        if top_cat == "disease":
            sci_name = SCIENTIFIC_TAXONOMY.get(condition_name)
            if not sci_name:
                for k, v in SCIENTIFIC_TAXONOMY.items():
                    if k.lower() in condition_name.lower():
                        sci_name = v
                        break
        # INVARIANT: If no scientific name is known, leave as None. Never fabricate synthetic Latin names.

        # Treatments from CIB&RC database
        treatments_catalog = self._lookup_treatments(diagnosed_crop, condition_name)

        if is_healthy:
            treatment_summary = (
                "Foliage is clinically healthy. No chemical intervention is warranted. "
                "Continue standard nutritional, irrigation, and balanced agronomic practices."
            )
            treatments_catalog.chemical = []
        elif treatments_catalog.chemical:
            top_chem = treatments_catalog.chemical[0]
            treatment_summary = (
                f"Apply CIB&RC registered {top_chem.chemical_name} at approved dosage of {top_chem.dosage} "
                "upon reaching Economic Threshold Level (ETL). Always observe recommended Pre-Harvest Intervals (PHI)."
            )
        else:
            treatment_summary = (
                f"No specific CIB&RC chemical fungicide is registered for {condition_name} on {diagnosed_crop}. "
                "Adopt preventive cultural and biological controls. Consult a local Krishi Vigyan Kendra (KVK) officer before applying any chemicals."
            )

        preventive_list = [
            "Maintain optimal plant spacing to promote canopy aeration and reduce relative humidity.",
            "Sterilize pruning shears and farm implements between plots to prevent mechanical transmission.",
            "Execute deep summer plowing to bury infected crop residues and expose resting spores to solar heat.",
            "Adopt crop rotation with non-host botanical families to disrupt fungal and bacterial cycles.",
        ]

        non_chem_list = [
            "Apply foliar bio-agents such as Trichoderma harzianum or Bacillus subtilis during early morning hours.",
            "Spray cold-pressed Neem seed kernel extract (NSKE 5%) or Azadirachtin 1500 ppm at initial symptom appearance.",
            "Prune and safely destroy heavily infected lower foliage before secondary conidial sporulation occurs.",
            "Avoid overhead sprinkler irrigation late in the evening to prevent prolonged leaf surface wetness.",
        ]

        description = (
            f"Diagnosed using {active_model_name}. Observed condition: '{condition_name}' "
            f"with {confidence_percent}% raw softmax classification score on host crop {diagnosed_crop}."
        )

        return DiseasePredictionResponse(
            condition=condition_name,
            scientific_name=sci_name,
            condition_type=condition_type,
            confidence=round(top_prob, 4),
            confidence_percent=confidence_percent,
            confidence_type="uncalibrated_softmax",
            severity=severity,
            is_healthy=is_healthy,
            is_supported=is_supported_crop,
            abstention=False,
            abstention_reason=None,
            abstention_threshold=threshold,
            diagnosed_crop=diagnosed_crop,
            host_crop_status=host_crop_status,
            crop_match=crop_match,
            crop_mismatch_warning=crop_mismatch_warning,
            description=description,
            treatment=treatment_summary,
            treatments=treatments_catalog,
            preventive_management=preventive_list,
            non_chemical_options=non_chem_list,
            top_5_predictions=top_5_list,
            top_disease_candidates=disease_candidates,
            top_pest_candidates=pest_candidates,
            model_type=active_model_name,
            model_identifier=active_model_name,
            routing_path="generalist_fallback",
            specialist_agreement=None,
            fusion_outcome="single_model",
            competing_predictions=[],
            fusion_details={
                "routing_path": "generalist_fallback",
                "fusion_outcome": "single_model",
                "specialist_model": None,
                "generalist_model": active_model_name,
                "concordance": "generalist_only",
                "notes": [f"No active specialist for crop '{crop}'. Evaluated by multi-crop generalist."],
            },
            raw_score=round(top_prob, 4),
            calibrated_confidence=round(top_prob, 4),
            provenance={
                "engine": self._active_engine_name,
                "weights_hash": self._primary_engine.weights_hash if self._primary_engine else "legacy_rollback",
                "latency_ms": round(latency_ms, 2),
                "device": "cpu",
                "abstention_threshold": threshold,
            },
            warnings=warnings_list,
        )


# Singleton instance
disease_detection_service = DiseaseDetectionService()

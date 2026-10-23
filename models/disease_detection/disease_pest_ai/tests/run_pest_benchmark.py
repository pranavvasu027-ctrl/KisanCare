"""
Legitimate Pest Benchmark Evaluation Suite (Phase 3 Sections 17, 18, 19, 20).

Evaluates the primary pest detector (underdogquality/yolo11s-pest-detection)
on legitimate test examples across distinct visual domains:
- Field Foliage (on-plant leaf)
- Pheromone Sticky Trap (Wadhwani Open Data)
- Disease Control Baseline (clean foliage / disease only)

Records:
- Image path
- Domain type: field | trap | lab | synthetic
- Ground truth annotations (if available)
- Predictions (classes, scores, bounding boxes)
- Latency (ms)
- Output metrics: True Negatives (clean foliage), Detections, False Positives
"""

import json
import time
from pathlib import Path
from PIL import Image

from disease_pest_ai.models.pest.yolo_pest_adapter import YoloPestAdapter

BENCHMARK_IMAGES = [
    {
        "filename": "wadhwani_cotton_trap_sample1.jpg",
        "domain": "trap",
        "image_type": "trap_sticky_sheet",
        "crop": "Cotton",
        "ground_truth": {
            "pest": "Pink Bollworm (pbw)",
            "boxes": [[337.79, 241.13, 356.58, 272.93]],
            "source": "Wadhwani AI BOLLWM dev.csv.gz (ICLR 2023)"
        }
    },
    {
        "filename": "wadhwani_cotton_trap.jpg",
        "domain": "trap",
        "image_type": "trap_sticky_sheet",
        "crop": "Cotton",
        "ground_truth": {
            "pest": "Cotton Bollworm (trap moths)",
            "boxes": None,
            "source": "Wadhwani AI Pest Monitoring Reference Image"
        }
    },
    {
        "filename": "corn_common_rust.jpg",
        "domain": "field",
        "image_type": "leaf",
        "crop": "Corn",
        "ground_truth": {
            "pest": "None (Foliar fungal rust pathology only)",
            "boxes": [],
            "source": "PlantVillage Corn Common Rust Field Macro"
        }
    },
    {
        "filename": "apple_scab_bierny.jpg",
        "domain": "field",
        "image_type": "leaf",
        "crop": "Apple",
        "ground_truth": {
            "pest": "None (Foliar fungal scab lesion only)",
            "boxes": [],
            "source": "BiernyVR Test Image (Apple Scab)"
        }
    },
    {
        "filename": "tomato_early_blight.jpg",
        "domain": "field",
        "image_type": "leaf",
        "crop": "Tomato",
        "ground_truth": {
            "pest": "None (Foliar Alternaria blight lesion only)",
            "boxes": [],
            "source": "PlantVillage Tomato Early Blight"
        }
    },
    {
        "filename": "tomato_healthy.jpg",
        "domain": "laboratory",
        "image_type": "leaf",
        "crop": "Tomato",
        "ground_truth": {
            "pest": "None (Healthy foliar tissue)",
            "boxes": [],
            "source": "PlantVillage Tomato Healthy Control"
        }
    }
]


def run_benchmark():
    test_dir = Path(__file__).resolve().parent.parent / "test_data"
    adapter = YoloPestAdapter(model_variant="primary")
    
    results = []
    total_latency = 0.0

    print(f"Executing legitimate pest detection benchmark on {len(BENCHMARK_IMAGES)} samples...")

    for item in BENCHMARK_IMAGES:
        img_p = test_dir / item["filename"]
        if not img_p.exists():
            print(f"Skipping missing image: {img_p}")
            continue

        t0 = time.perf_counter()
        pred = adapter.predict(
            image=img_p,
            crop_name=item["crop"],
            image_type=item["image_type"]
        )
        lat = (time.perf_counter() - t0) * 1000
        total_latency += lat

        detected_list = []
        for p in pred.pests:
            detected_list.append({
                "pest": p.pest,
                "score": round(p.score, 4),
                "box": [round(c, 2) for c in p.bounding_box],
                "crop_compatible": p.crop_compatible
            })

        entry = {
            "filename": item["filename"],
            "domain": item["domain"],
            "image_type": item["image_type"],
            "crop": item["crop"],
            "ground_truth": item["ground_truth"],
            "latency_ms": round(lat, 2),
            "status": pred.status,
            "detected_pests": detected_list,
            "pest_count": len(detected_list),
            "warnings": pred.warnings
        }
        results.append(entry)
        print(f"[{item['domain'].upper()}] {item['filename']} -> {len(detected_list)} pests detected ({lat:.1f} ms)")

    avg_lat = total_latency / len(results) if results else 0.0

    summary = {
        "model_name": adapter.model_name,
        "model_version": adapter.model_version,
        "total_samples": len(results),
        "average_cpu_latency_ms": round(avg_lat, 2),
        "results": results
    }

    out_json = test_dir / "pest_benchmark_results.json"
    with open(out_json, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)

    print(f"Benchmark completed successfully! Average CPU latency: {avg_lat:.2f} ms")
    print(f"Saved results to: {out_json}")


if __name__ == "__main__":
    run_benchmark()

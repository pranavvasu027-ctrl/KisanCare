"""Download independent labelled soybean benchmark images."""

import json
import os
import urllib.request

eval_dir = os.path.join("models", "disease_detection", "test_data", "soybean_eval")
os.makedirs(eval_dir, exist_ok=True)

manifest = []

# 1. Fetch from anandvermagmailcom/soybean-leaf-diseases
# Frogeye: offset 300 (label 1)
# Healthy: offset 600 (label 2)
# Soybean Rust: offset 1000 (label 3)
# Bacterial Blight (OOD control): offset 20 (label 0)
targets_anand = [
    {"offset": 300, "label": 1, "cls_name": "Frogeye Leaf Spot", "prefix": "frogeye_leaf_spot"},
    {"offset": 600, "label": 2, "cls_name": "Healthy Foliage", "prefix": "healthy_foliage"},
    {"offset": 1000, "label": 3, "cls_name": "Asian Soybean Rust", "prefix": "soybean_rust"},
    {"offset": 20, "label": 0, "cls_name": "Bacterial Blight (OOD)", "prefix": "bacterial_blight_ood"},
]

for tgt in targets_anand:
    url = f"https://datasets-server.huggingface.co/rows?dataset=anandvermagmailcom%2Fsoybean-leaf-diseases&config=default&split=train&offset={tgt['offset']}&limit=20"
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    try:
        with urllib.request.urlopen(req) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            count = 0
            for r in data.get("rows", []):
                lbl = r["row"]["label"]
                if lbl == tgt["label"] and count < 4:
                    count += 1
                    fname = f"{tgt['prefix']}_{count}.jpg"
                    fpath = os.path.join(eval_dir, fname)
                    img_url = r["row"]["image"]["src"]
                    urllib.request.urlretrieve(img_url, fpath)
                    manifest.append({
                        "image_path": fpath.replace("\\", "/"),
                        "ground_truth": tgt["cls_name"],
                        "crop": "Soybean",
                        "source": "anandvermagmailcom/soybean-leaf-diseases",
                    })
                    print(f"Saved {fname} for {tgt['cls_name']}")
    except Exception as exc:
        print(f"Error fetching {tgt['cls_name']}: {exc}")

# 2. Fetch from Project-AgML/soybean_leaf_disease_classification
# Septoria Brown Spot: offset 400 (label 4)
url_agml = "https://datasets-server.huggingface.co/rows?dataset=Project-AgML%2Fsoybean_leaf_disease_classification&config=default&split=train&offset=400&limit=20"
req_agml = urllib.request.Request(url_agml, headers={"User-Agent": "Mozilla/5.0"})
try:
    with urllib.request.urlopen(req_agml) as resp:
        data_agml = json.loads(resp.read().decode("utf-8"))
        count_septoria = 0
        for r in data_agml.get("rows", []):
            lbl = r["row"]["label"]
            if lbl == 4 and count_septoria < 4:
                count_septoria += 1
                fname = f"septoria_brown_spot_{count_septoria}.jpg"
                fpath = os.path.join(eval_dir, fname)
                img_url = r["row"]["image"]["src"]
                urllib.request.urlretrieve(img_url, fpath)
                manifest.append({
                    "image_path": fpath.replace("\\", "/"),
                    "ground_truth": "Brown Spot (Septoria)",
                    "crop": "Soybean",
                    "source": "Project-AgML/soybean_leaf_disease_classification",
                })
                print(f"Saved {fname} for Brown Spot (Septoria)")
except Exception as exc:
    print(f"Error fetching Septoria from AgML: {exc}")

manifest_path = os.path.join(eval_dir, "manifest.json")
with open(manifest_path, "w", encoding="utf-8") as f:
    json.dump(manifest, f, indent=2)

print(f"Total soybean benchmark images downloaded: {len(manifest)}")

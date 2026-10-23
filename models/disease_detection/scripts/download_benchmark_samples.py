"""Download representative benchmark samples for cotton disease evaluation."""

import json
import os
import urllib.request

eval_dir = os.path.join("models", "disease_detection", "test_data", "cotton_eval")
os.makedirs(eval_dir, exist_ok=True)

manifest = []

targets = [
    {"offset": 1200, "target_lbl": 1, "cls_name": "Bacterial Blight", "prefix": "bacterial_blight"},
    {"offset": 1000, "target_lbl": 2, "cls_name": "Fusarium Wilt", "prefix": "fusarium_wilt"},
    {"offset": 600, "target_lbl": 3, "cls_name": "Healthy Foliage", "prefix": "healthy_foliage"},
]

for tgt in targets:
    url = f"https://datasets-server.huggingface.co/rows?dataset=Project-AgML%2Fcotton_leaf_disease_classification&config=raw&split=train&offset={tgt['offset']}&limit=10"
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    try:
        with urllib.request.urlopen(req) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            count = 0
            for r in data.get("rows", []):
                lbl = r["row"]["label"]
                if lbl == tgt["target_lbl"] and count < 4:
                    count += 1
                    fname = f"{tgt['prefix']}_{count}.jpg"
                    fpath = os.path.join(eval_dir, fname)
                    img_url = r["row"]["image"]["src"]
                    urllib.request.urlretrieve(img_url, fpath)
                    manifest.append({
                        "image_path": fpath.replace("\\", "/"),
                        "ground_truth": tgt["cls_name"],
                        "crop": "Cotton",
                        "source": "Project-AgML/cotton_leaf_disease_classification",
                    })
                    print(f"Saved {fname} for {tgt['cls_name']}")
    except Exception as exc:
        print(f"Error fetching {tgt['cls_name']}: {exc}")

# Bangladesh 2 for Curl Virus (label=1)
url2 = "https://datasets-server.huggingface.co/rows?dataset=Project-AgML%2Fcotton_leaf_disease_classification_bangladesh_2&config=raw&split=train&offset=260&limit=10"
req2 = urllib.request.Request(url2, headers={"User-Agent": "Mozilla/5.0"})
try:
    with urllib.request.urlopen(req2) as resp:
        data2 = json.loads(resp.read().decode("utf-8"))
        curl_count = 0
        for r in data2.get("rows", []):
            lbl = r["row"]["label"]
            if lbl == 1 and curl_count < 4:
                curl_count += 1
                fname = f"curl_virus_{curl_count}.jpg"
                fpath = os.path.join(eval_dir, fname)
                img_url = r["row"]["image"]["src"]
                urllib.request.urlretrieve(img_url, fpath)
                manifest.append({
                    "image_path": fpath.replace("\\", "/"),
                    "ground_truth": "Cotton Leaf Curl Virus",
                    "crop": "Cotton",
                    "source": "Project-AgML/cotton_leaf_disease_classification_bangladesh_2",
                })
                print(f"Saved {fname} for Cotton Leaf Curl Virus")
except Exception as exc:
    print(f"Error fetching Curl Virus: {exc}")

# Local field images
manifest.append({
    "image_path": "frontend/public/test_images/cotton_leaf_spot.jpg",
    "ground_truth": "Bacterial Blight",
    "crop": "Cotton",
    "source": "local_field_leaf",
})
manifest.append({
    "image_path": "frontend/public/test_images/cotton_field_leaf.jpg",
    "ground_truth": "Bacterial Blight",
    "crop": "Cotton",
    "source": "local_field_leaf",
})

manifest_path = os.path.join(eval_dir, "manifest.json")
with open(manifest_path, "w", encoding="utf-8") as f:
    json.dump(manifest, f, indent=2)

print(f"Total benchmark images prepared: {len(manifest)}")

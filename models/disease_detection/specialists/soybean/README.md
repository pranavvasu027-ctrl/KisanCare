# Soybean Crop Disease Specialist Model (`ixrbhii/soybean-disease-convnext`)

## 1. Overview & Provenance

- **Model Identifier:** `ixrbhii/soybean-disease-convnext`
- **Architecture:** ConvNeXt-Small (`timm` implementation)
- **Parameters:** ~50.2M parameters
- **License:** Creative Commons Attribution 4.0 International (CC-BY-4.0)
- **Hugging Face Repository:** https://huggingface.co/ixrbhii/soybean-disease-convnext
- **Status:** `active` (Registered in `specialists_config.json`, `PRELIMINARY_EVALUATION` status)

## 2. Checkpoint Artifact & Integrity

In accordance with KisanCare repository policy, large pre-trained model weights are excluded from Git version control via `.gitignore` (`*.safetensors`, `*.bin`, `*.pth`, `*.pt`).

- **Artifact Filename:** `model.safetensors`
- **Artifact Size:** 94.37 MB (98,958,848 bytes)
- **Relative Path:** `models/disease_detection/specialists/soybean/model.safetensors`
- **Cryptographic SHA-256 Fingerprint:**
  ```
  41f79f767719150bfe8e4574fd4c299fdbcfaa7a924923cb630ad055a57a6f0f
  ```

## 3. Retrieval & Installation Instructions

To download the verified model weights directly from Hugging Face:

```bash
# Using huggingface_hub Python SDK
python -c "from huggingface_hub import hf_hub_download; hf_hub_download(repo_id='ixrbhii/soybean-disease-convnext', filename='model.safetensors', local_dir='models/disease_detection/specialists/soybean')"
```

Or download manually via CLI:
```bash
curl -L -o models/disease_detection/specialists/soybean/model.safetensors https://huggingface.co/ixrbhii/soybean-disease-convnext/resolve/main/model.safetensors
```

Verify integrity with PowerShell:
```powershell
Get-FileHash -Algorithm SHA256 models/disease_detection/specialists/soybean/model.safetensors
# Hash must match: 41F79F767719150BFE8E4574FD4C299FDCFCAA7A924923CB630AD055A57A6F0F
```

## 4. Supported Classes & Canonical Normalization

The model classifies 6 foliar conditions mapped to canonical KisanCare project taxonomy:

| Index | Checkpoint Label | Canonical Label | Scientific Latin Nomenclature | Category |
| :---: | :--- | :--- | :--- | :--- |
| 0 | `Downy Mildew` | `soybean::Downy mildew` | *Peronospora manshurica* | Disease |
| 1 | `Frogeye Leaf Spot` | `soybean::Frogeye leaf spot` | *Cercospora sojina* | Disease |
| 2 | `Healthy` | `soybean::Healthy` | Healthy Foliage | Healthy |
| 3 | `Mosaic Virus` | `soybean::Mosaic virus` | *Soybean mosaic virus* (SMV) | Disease |
| 4 | `Rust` | `soybean::Rust` | *Phakopsora pachyrhizi* (Asian Rust) | Disease |
| 5 | `Septoria Brown Spot` | `soybean::Septoria brown spot` | *Septoria glycines* | Disease |

### Out-of-Distribution Safety Guard
Any class outside these 6 verified classes (such as Bacterial Blight, Charcoal Rot, or Stem Canker) is rejected by the adapter and forces clinical abstention in the Intelligent Router.

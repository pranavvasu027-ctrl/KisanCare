"""
Build script to generate normalized treatments.json conforming strictly to schema.json.
"""

import json
from pathlib import Path

SOURCE_CIBRC = "SRC-CIBRC-2024"
DATE_CIBRC = "2024-03-31"

SOURCE_IPM = "SRC-DPPQS-IPM-2022"
DATE_IPM = "2022-06-15"

VERIF_DATE = "2026-10-04"


def build_treatments():
    # Load previously built raw records from cibrc_database.json and map them to schema.json format
    db_file = Path(__file__).resolve().parent / "cibrc_database.json"
    with open(db_file, "r", encoding="utf-8") as f:
        raw_recs = json.load(f)

    treatments = []
    for r in raw_recs:
        # Determine source_id
        src_id = SOURCE_CIBRC if "CIBRC" in r["id"] else SOURCE_IPM
        if "NCIPM" in r.get("source_title", ""):
            src_id = "SRC-ICAR-NCIPM-2023"
        elif "CITH" in r.get("source_title", ""):
            src_id = "SRC-ICAR-CITH-2023"
        elif "NRC" in r.get("source_title", ""):
            src_id = "SRC-ICAR-NRCG-2023"
        elif "CCRI" in r.get("source_title", ""):
            src_id = "SRC-ICAR-CCRI-2023"

        # Determine target biological pathogen / agent
        target = r.get("approved_target", r["condition"])

        # Parse numerical dose and dose_unit safely without inventing
        raw_dose = r.get("dose_information", "")
        dose = None
        dose_unit = None
        phi = None

        if "1.5-2.0 kg/ha" in raw_dose:
            dose = "1.5-2.0"
            dose_unit = "kg/ha"
        elif "250-500 ml/ha" in raw_dose:
            dose = "250-500"
            dose_unit = "ml/ha"
        elif "1500-1750 g/ha" in raw_dose:
            dose = "1500-1750"
            dose_unit = "g/ha"
        elif "2.5 kg/ha" in raw_dose:
            dose = "2.5"
            dose_unit = "kg/ha"
        elif "1.0 kg/ha" in raw_dose:
            dose = "1.0"
            dose_unit = "kg/ha"
        elif "625 ml/ha" in raw_dose:
            dose = "625"
            dose_unit = "ml/ha"
        elif "1.25-1.5 kg/ha" in raw_dose:
            dose = "1.25-1.5"
            dose_unit = "kg/ha"
        elif "600 g/ha" in raw_dose:
            dose = "600"
            dose_unit = "g/ha"
        elif "1.0-1.5 kg/ha" in raw_dose:
            dose = "1.0-1.5"
            dose_unit = "kg/ha"
        elif "500 ml/ha" in raw_dose:
            dose = "500"
            dose_unit = "ml/ha"
        elif "0.25%" in raw_dose:
            dose = "0.25%"
            dose_unit = "concentration (250 g/100 L)"
        elif "0.03%" in raw_dose:
            dose = "0.03%"
            dose_unit = "concentration (30 ml/100 L)"
        elif "0.1%" in raw_dose:
            dose = "0.1%"
            dose_unit = "concentration (100 g/100 L)"
        elif "0.2%" in raw_dose:
            dose = "0.2%"
            dose_unit = "concentration (200 g/100 L)"
        elif "50 ml in 100 L" in raw_dose:
            dose = "50"
            dose_unit = "ml/100 L water"
        elif "150 ml/ha" in raw_dose:
            dose = "150"
            dose_unit = "ml/ha"
        elif "190-220 g/ha" in raw_dose:
            dose = "190-220"
            dose_unit = "g/ha"
        elif "10-15 yellow sticky traps" in raw_dose:
            dose = "10-15"
            dose_unit = "traps/acre"
        elif "5 traps/ha" in raw_dose:
            dose = "5"
            dose_unit = "traps/ha"
        elif "150,000 parasitoids/ha" in raw_dose:
            dose = "150000"
            dose_unit = "parasitoids/ha"

        # Parse PHI if documented in safety_notes
        s_notes = r.get("safety_notes") or ""
        if "Waiting period (PHI): 3 days" in s_notes or "Waiting period: 3 days" in s_notes:
            phi = 3
        elif "Waiting period (PHI): 5 days" in s_notes or "Waiting period: 5 days" in s_notes:
            phi = 5
        elif "Waiting period: 7 days" in s_notes:
            phi = 7
        elif "Waiting period: 10 days" in s_notes:
            phi = 10
        elif "Waiting period: 14 days" in s_notes:
            phi = 14
        elif "Waiting period: 9 days" in s_notes:
            phi = 9

        item = {
            "id": r["id"],
            "crop": r["crop"],
            "condition": r["condition"],
            "condition_type": r["condition_type"],
            "target": target,
            "active_ingredient": r["active_ingredient"],
            "formulation": r["formulation"],
            "registered_use": r["registered_use"],
            "approved_crop": r["approved_crop"],
            "approved_target": r["approved_target"],
            "application_method": r.get("application_method"),
            "dose": dose,
            "dose_unit": dose_unit,
            "pre_harvest_interval": phi,
            "number_of_applications": None,  # Null when not explicitly capped on CIBRC register
            "interval": None,                # Null when not specified
            "region_scope": r.get("region", "India"),
            "source_id": src_id,
            "source_date": r["source_date"],
            "verification_date": r.get("verification_date", VERIF_DATE),
            "verification_status": r.get("verification_status", "verified"),
            "notes": r.get("notes"),
            "safety_notes": r.get("safety_notes"),
        }
        treatments.append(item)

    out_file = Path(__file__).resolve().parent / "treatments.json"
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(treatments, f, indent=2, ensure_ascii=False)
    print(f"Generated {len(treatments)} normalized treatment records in {out_file}")


if __name__ == "__main__":
    build_treatments()

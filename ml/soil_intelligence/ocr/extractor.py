"""
Multi-Format Laboratory Report Extractor
========================================
Parses PDF, JPG, and PNG laboratory soil test reports.
Extracts report headers, sample dates, plot identifiers, and soil test parameters.
Calculates field-level confidence scores and flags uncertain readings for review.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Tuple
import os
import re
from datetime import datetime

from ml.soil_intelligence.schemas import (
    MeasuredLaboratoryReport,
    NutrientMeasurement,
    ProvenanceType,
    TestMethod
)
from ml.soil_intelligence.ocr.normalizer import (
    ReportFieldNormalizer,
    FieldNormalizationResult,
    ValidationIssue
)


@dataclass
class ExtractedReportDocument:
    file_path: str
    file_type: str                           # 'PDF', 'JPG', 'PNG'
    raw_text: str
    overall_confidence: float               # [0.0, 1.0]
    extracted_report: Optional[MeasuredLaboratoryReport]
    requires_human_review: bool
    field_confidences: Dict[str, float] = field(default_factory=dict)
    validation_issues: List[ValidationIssue] = field(default_factory=list)
    extraction_timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())

    def to_dict(self) -> Dict[str, Any]:
        return {
            "file_path": self.file_path,
            "file_type": self.file_type,
            "overall_confidence": round(self.overall_confidence, 3),
            "requires_human_review": self.requires_human_review,
            "field_confidences": {k: round(v, 3) for k, v in self.field_confidences.items()},
            "validation_issues": [
                {
                    "field": iss.field_name,
                    "value": str(iss.reported_value),
                    "severity": iss.severity,
                    "code": iss.issue_code,
                    "message": iss.message
                }
                for iss in self.validation_issues
            ],
            "extracted_report": self.extracted_report.to_dict() if self.extracted_report else None,
            "extraction_timestamp": self.extraction_timestamp
        }


class LabReportExtractor:
    """
    Ingests and parses digital/scanned laboratory soil reports.
    """

    # Common regex patterns found in Indian Soil Health Cards & private labs
    PATTERNS = {
        "lab_name": [
            r"(?:soil\s+testing\s+laboratory|district\s+soil\s+testing\s+lab|icar|kvk|krishi\s+vigyan\s+kendra)[^\n\r,]+",
            r"(?:department\s+of\s+agriculture[^\n\r]+)",
            r"([A-Za-z0-9\s]+(?:Laboratories|Lab|Testing\s+Center))"
        ],
        "sample_id": [
            r"(?:sample\s+(?:no|id|number|code)|certificate\s+no|report\s+(?:no|id)|lab\s+no|shc\s+no)[\s:=|]+([A-Za-z0-9\/\-_]+)",
            r"(MH[0-9]{5,10}\/[0-9\-_]+\/[0-9]+)",  # Standard Maharashtra SHC sample barcode
            r"\b([A-Za-z]{2,5}-[A-Za-z0-9]+-[0-9]{2,5})\b",  # Structured format like KSC-TEST-001 or SAT-2026-031
            r"(?:report\s+id)[:\.\s]+([A-Za-z0-9\-_]+)"
        ],
        "date": [
            r"(?:collection\s+date|sample\s+date|test\s+date|date\s+of\s+testing|date\s+of\s+collection|analysis\s+date|date)[\s:=|]+([0-9]{1,2}[\s\-\/\.](?:[A-Za-z]+|[0-9]{1,2})[\s\-\/\.][0-9]{2,4})",
            r"([0-9]{1,2}[\s\-\/\.][A-Za-z]{3,9}[\s\-\/\.][0-9]{2,4})",
            r"(20[1-2][0-9]-[0-2][0-9])"             # Cycle string like 2016-17 or 2024-25
        ],
        "plot_id": [
            r"(?:farm\s*\/\s*plot|plot\s+(?:no|id)|survey\s+(?:no|number)|field\s+(?:id|name)|parcel)[\s:=|]+([A-Za-z0-9\-_]+(?:\s+[A-Za-z0-9\-_]+)*?)(?=\s+(?:collection|farmer|village|date|district|owner|crop|document|\b)|$)",
            r"(?:field)[\s:=|]+([A-Za-z0-9\-_]+(?:\s+[A-Za-z0-9\-_]+)*?)(?=\s+(?:collection|farmer|village|date|district|owner|crop|document|\b)|$)"
        ],
        "pH": [
            r"(?:soil\s+reaction(?:\s*\([^\)]*\))?|soil\s+ph)(?:\s*\((?:1:2(?:\.5)?|soil-water|suspension|[^\)]*)\))*[\s:=|~-]+([0-9]+(?:[\.,][0-9]+)?)",
            r"(?:\bph\b|\bp\.h\.?\b|\bph\s+value\b)(?:\s*\((?:1:2(?:\.5)?|soil-water|suspension|[^\)]*)\))*[\s:=|~-]+([0-9]+(?:[\.,][0-9]+)?)",
            r"(?:\bph\b|\bp\.h\.?\b)\s*(?:index|scale)?[\s:=|~-]+([0-9]+(?:[\.,][0-9]+)?)",
            r"\b(?:ph|p\.h\.?)\b[^\n\r0-9]{1,25}?([0-9]+(?:[\.,][0-9]+)?)(?:\s*(?:phindex|index|scale|\b))"
        ],
        "EC": [
            r"(?:electrical\s+conductivity(?:\s*\([^\)]*\))?|e\.c\.|ec)[\s:=|~-]+([0-9]+(?:[\.,][0-9]+)?)",
            r"\bEC[\s:=|~-]+([0-9]+(?:[\.,][0-9]+)?)"
        ],
        "OC": [
            r"(?:organic\s+c[ao]rbon(?:\s*\([^\)]*\))?|o\.c\.|oc)[\s:=|~-]+([0-9]+(?:[\.,][0-9]+)?)",
            r"\bOC[\s:=|~-]+([0-9]+(?:[\.,][0-9]+)?)"
        ],
        "N": [
            r"(?:available|avail[aoe]ble|avallable)\s+(?:nitrogen|n)(?:\s*\((?:as|os)?\s*n\))?(?:\s*\([^\)]*\))?[\s:=|~-]+([0-9]+(?:[\.,][0-9]+)?)",
            r"(?:nitrogen)(?:\s*\((?:as|os)?\s*n\))?(?:\s*\([^\)]*\))?[\s:=|~-]+([0-9]+(?:[\.,][0-9]+)?)",
            r"\bN\b(?:\s*\([^)]*\))?[\s:=|~-]+([0-9]+(?:[\.,][0-9]+)?)",
            r"(?:nitrogen|\bn\b)[^\n\r0-9]{1,35}?([0-9]+(?:[\.,][0-9]+)?)\s*(?:kg/ha|kgyha|koyha|kg\.ha|ko/ha|mg/kg|ppm)"
        ],
        "P": [
            r"(?:available|avail[aoe]ble|avallable|avalleble|avol[lo]ble)\s+(?:phosphorus|p2[o0]5|p₂o₅|phosphate|p)(?:\s*\((?:as|os|o9|ios)?\s*p[2o0]*\))?(?:\s*\([^\)]*\))?[\s:=|~-]+([0-9]+(?:[\.,][0-9]+)?)",
            r"(?:phosphorus|phosphate)(?:\s*\((?:as|os|o9|ios)?\s*p[2o0]*\))?(?:\s*\([^\)]*\))?[\s:=|~-]+([0-9]+(?:[\.,][0-9]+)?)",
            r"(?:p2[o0]5|p₂o₅)(?:\s*\([^\)]*\))?[\s:=|~-]+([0-9]+(?:[\.,][0-9]+)?)",
            r"\bP\b(?:\s*\([^)]*\))?[\s:=|~-]+([0-9]+(?:[\.,][0-9]+)?)",
            r"(?:phosphorus|phosphate|p2[o0]5|p₂o₅|\bp\b)[^\n\r0-9]{1,35}?([0-9]+(?:[\.,][0-9]+)?)\s*(?:kg/ha|kgyha|koyha|kg\.ha|ko/ha|mg/kg|ppm)"
        ],
        "K": [
            r"(?:available|avail[aoe]ble|avallable|avalleble|avaltoble|avateble)\s+(?:potassium|pot[ao]ss[il1u]um[k]?|potash|k[2o0]*)(?:\s*\((?:as|os)?\s*k[2o0]*\))?(?:\s*\([^\)]*\))?[\s:=|~-]+([0-9]+(?:[\.,][0-9]+)?)",
            r"(?:potassium|pot[ao]ss[il1u]um[k]?|potash)(?:\s*\((?:as|os)?\s*k[2o0]*\))?(?:\s*\([^\)]*\))?[\s:=|~-]+([0-9]+(?:[\.,][0-9]+)?)",
            r"(?:available|avail[aoe]ble|avail)\s+k[2o0]*(?:\s*\([^\)]*\))?[\s:=|~-]+([0-9]+(?:[\.,][0-9]+)?)",
            r"\bK\b(?:\s*\([^)]*\))?[\s:=|~-]+([0-9]+(?:[\.,][0-9]+)?)",
            r"(?:k2[o0]|k₂o)(?:\s*\([^\)]*\))?[\s:=|~-]+([0-9]+(?:[\.,][0-9]+)?)",
            r"(?:potassium|pot[ao]ss[il1u]um[k]?|potash|\bk\b)[^\n\r0-9]{1,35}?([0-9]+(?:[\.,][0-9]+)?)\s*(?:kg/ha|kgyha|koyha|kg\.ha|ko/ha|mg/kg|ppm)"
        ]
    }

    @classmethod
    def extract_from_text(
        cls,
        text_content: str,
        source_file_path: str = "direct_text_input",
        file_type: str = "TEXT"
    ) -> ExtractedReportDocument:
        """
        Parses raw text extracted from a report document into structured, validated fields.
        """
        lines = [line.strip() for line in text_content.splitlines() if line.strip()]
        flat_text = " ".join(lines)
        field_confidences: Dict[str, float] = {}
        all_issues: List[ValidationIssue] = []

        # 1. Extract Lab Name
        lab_name = "Government / Certified Soil Testing Laboratory"
        for pat in cls.PATTERNS["lab_name"]:
            m = re.search(pat, flat_text, re.IGNORECASE)
            if m:
                lab_name = m.group(0).strip()
                field_confidences["lab_name"] = 0.95
                break
        if "lab_name" not in field_confidences:
            field_confidences["lab_name"] = 0.60

        # 2. Extract Sample / Report ID
        report_id = None
        DISALLOWED_SAMPLE_IDS = {
            "collection", "date", "farmer", "name", "plot", "field", "location",
            "document", "type", "soil", "report", "parameters", "test", "status",
            "table", "value", "unit", "method", "analytical"
        }
        for pat in cls.PATTERNS["sample_id"]:
            for m in re.finditer(pat, flat_text, re.IGNORECASE):
                cand = m.group(1).strip()
                if cand.lower() not in DISALLOWED_SAMPLE_IDS and len(cand) >= 3:
                    report_id = cand
                    field_confidences["report_id"] = 0.95
                    break
            if report_id:
                break

        if not report_id:
            report_id = "UNKNOWN_SAMPLE_ID"
            field_confidences["report_id"] = 0.0
            all_issues.append(ValidationIssue(
                field_name="report_id",
                reported_value=report_id,
                severity="WARNING",
                issue_code="MISSING_REPORT_ID",
                message="Report sample identifier could not be matched with high confidence."
            ))

        # 3. Extract Date
        sample_date = None
        raw_date_str = None
        for pat in cls.PATTERNS["date"]:
            m = re.search(pat, flat_text, re.IGNORECASE)
            if m:
                raw_date_str = m.group(1).strip()
                break

        if raw_date_str:
            sample_date = raw_date_str
            field_confidences["sample_date"] = 0.90
        else:
            field_confidences["sample_date"] = 0.0
            all_issues.append(ValidationIssue(
                field_name="sample_date",
                reported_value=None,
                severity="INFO",
                issue_code="DATE_NOT_DETECTED",
                message="Sample collection/testing date was not detected in report document."
            ))

        # 4. Extract Plot ID (check individual lines first to avoid cross-line token bleed)
        plot_id = "PLOT_DEFAULT"
        for line in lines:
            for pat in cls.PATTERNS["plot_id"]:
                m = re.search(pat, line, re.IGNORECASE)
                if m:
                    plot_id = m.group(1).strip()
                    field_confidences["plot_id"] = 0.90
                    break
            if "plot_id" in field_confidences:
                break

        if "plot_id" not in field_confidences:
            for pat in cls.PATTERNS["plot_id"]:
                m = re.search(pat, flat_text, re.IGNORECASE)
                if m:
                    plot_id = m.group(1).strip()
                    field_confidences["plot_id"] = 0.85
                    break

        if "plot_id" not in field_confidences:
            field_confidences["plot_id"] = 0.50

        PARAM_LABELS = {
            "pH": r"^(?:soil\s+reaction|soil\s+ph|ph\s+value|ph|p\.h\.)(?:\s*\([^\)]*\))*$",
            "EC": r"^(?:electrical\s+conductivity|ec|e\.c\.)(?:\s*\([^\)]*\))?$",
            "OC": r"^(?:organic\s+c[ao]rbon|oc|o\.c\.)(?:\s*\([^\)]*\))?$",
            "N": r"^(?:available\s+nitrogen|avail[aoe]ble\s+nitrogen|nitrogen|avail\s+n|\bn\b)(?:\s*\([^\)]*\))?$",
            "P": r"^(?:available\s+phosphorus|avail[aoe]ble\s+phosphorus|phosphorus|avail\s+p|available\s+p2[o0]5|p2[o0]5|p₂o₅|\bp\b)(?:\s*\([^\)]*\))?$",
            "K": r"^(?:available\s+potassium|avail[aoe]ble\s+pot[ao]ss[il1u]um[k]?|avail[aoe]ble\s+potash|available\s+k2[o0]|potassium|potash|avail\s+k|k2[o0]|k₂o|\bk\b)(?:\s*\([^\)]*\))?$"
        }

        # Helper to extract and normalize a parameter
        def extract_param(param_key: str, patterns: List[str]) -> Tuple[Optional[FieldNormalizationResult], float]:
            # Strategy 1: Search line-by-line first (highest accuracy on table rows, eliminates cross-line bleed)
            for line in lines:
                for pat in patterns:
                    m = re.search(pat, line, re.IGNORECASE)
                    if m:
                        raw_val = m.group(1)
                        res = ReportFieldNormalizer.normalize_nutrient_field(
                            nutrient=param_key,
                            raw_val_str=raw_val,
                            surrounding_text=line
                        )
                        if res.measurement:
                            conf = 0.98 if res.is_plausible else 0.70
                            return res, conf

            # Strategy 2: Search in flat text with robust regex
            for pat in patterns:
                m = re.search(pat, flat_text, re.IGNORECASE)
                if m:
                    raw_val = m.group(1)
                    start = max(0, m.start() - 25)
                    end = min(len(flat_text), m.end() + 35)
                    surrounding = flat_text[start:end]
                    res = ReportFieldNormalizer.normalize_nutrient_field(
                        nutrient=param_key,
                        raw_val_str=raw_val,
                        surrounding_text=surrounding
                    )
                    if res.measurement:
                        conf = 0.95 if res.is_plausible else 0.65
                        return res, conf

            # Strategy 3: Multi-line adjacent check (line i has label, line i+1 or i+2 has number)
            lbl_pat = PARAM_LABELS.get(param_key)
            if lbl_pat:
                for idx, line in enumerate(lines):
                    if re.search(lbl_pat, line, re.IGNORECASE):
                        for offset in (1, 2):
                            if idx + offset < len(lines):
                                cand_line = lines[idx + offset].strip()
                                if re.search(r"^(?:reported|value|unit|form|method|parameter|table)", cand_line, re.IGNORECASE):
                                    continue
                                m_num = re.search(r"^([0-9]+(?:[\.,][0-9]+)?)\b", cand_line)
                                if m_num:
                                    raw_val = m_num.group(1)
                                    ctx = " ".join(lines[max(0, idx - 1):min(len(lines), idx + 4)])
                                    res = ReportFieldNormalizer.normalize_nutrient_field(
                                        nutrient=param_key,
                                        raw_val_str=raw_val,
                                        surrounding_text=ctx
                                    )
                                    if res.measurement:
                                        conf = 0.90 if res.is_plausible else 0.60
                                        return res, conf

            return None, 0.0

        # Extract N, P, K
        res_n, conf_n = extract_param("N", cls.PATTERNS["N"])
        field_confidences["nitrogen"] = conf_n
        if res_n: all_issues.extend(res_n.issues)

        res_p, conf_p = extract_param("P", cls.PATTERNS["P"])
        field_confidences["phosphorus"] = conf_p
        if res_p: all_issues.extend(res_p.issues)

        res_k, conf_k = extract_param("K", cls.PATTERNS["K"])
        field_confidences["potassium"] = conf_k
        if res_k: all_issues.extend(res_k.issues)

        # Extract pH, EC, OC
        res_ph, conf_ph = extract_param("pH", cls.PATTERNS["pH"])
        field_confidences["pH"] = conf_ph
        if res_ph: all_issues.extend(res_ph.issues)

        res_ec, conf_ec = extract_param("EC", cls.PATTERNS["EC"])
        field_confidences["EC"] = conf_ec
        if res_ec: all_issues.extend(res_ec.issues)

        res_oc, conf_oc = extract_param("OC", cls.PATTERNS["OC"])
        field_confidences["OC"] = conf_oc
        if res_oc: all_issues.extend(res_oc.issues)

        # Compute overall confidence
        core_fields = ["nitrogen", "phosphorus", "potassium", "pH"]
        core_confs = [field_confidences.get(k, 0.0) for k in core_fields]
        avg_core_conf = sum(core_confs) / len(core_confs)

        meta_fields = ["report_id", "sample_date"]
        meta_confs = [field_confidences.get(k, 0.0) for k in meta_fields]
        avg_meta_conf = sum(meta_confs) / len(meta_confs)

        # 80% weight on core agronomic nutrients, 20% on metadata
        overall_conf = round(0.80 * avg_core_conf + 0.20 * avg_meta_conf, 3)

        # Flag human review if core fields missing or overall confidence low or issues
        missing_core = any(field_confidences.get(k, 0.0) == 0.0 for k in core_fields)
        requires_review = missing_core or (overall_conf < 0.85) or any(iss.severity == "ERROR" for iss in all_issues) or len(all_issues) > 0

        # Construct MeasuredLaboratoryReport
        report = MeasuredLaboratoryReport(
            report_id=report_id,
            plot_id=plot_id,
            sample_date=sample_date,
            lab_name=lab_name,
            lab_certificate_no=report_id,
            provenance=ProvenanceType.MEASURED,
            nitrogen=res_n.measurement if res_n else None,
            phosphorus=res_p.measurement if res_p else None,
            potassium=res_k.measurement if res_k else None,
            ph=res_ph.measurement.reported_value if (res_ph and res_ph.measurement) else None,
            ec_ds_m=res_ec.measurement.reported_value if (res_ec and res_ec.measurement) else None,
            organic_carbon_pct=res_oc.measurement.reported_value if (res_oc and res_oc.measurement) else None,
            extraction_confidence=round(overall_conf, 3),
            review_required=requires_review,
            notes=f"Parsed from {file_type} document: {os.path.basename(source_file_path)}"
        )

        return ExtractedReportDocument(
            file_path=source_file_path,
            file_type=file_type,
            raw_text=text_content,
            overall_confidence=round(overall_conf, 3),
            extracted_report=report,
            requires_human_review=requires_review,
            field_confidences=field_confidences,
            validation_issues=all_issues
        )

    @classmethod
    def ingest_file(cls, file_path: str) -> ExtractedReportDocument:
        """
        Ingests a laboratory report file (PDF, JPG, PNG) and executes OCR/parsing.
        Handles text-layer extraction for digital PDFs and provides hooks for scanned OCR.
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Laboratory report file does not exist: {file_path}")

        ext = os.path.splitext(file_path)[1].lower()

        # Digital PDF parser
        if ext == ".pdf":
            raw_text = ""
            # Fallback 1: Attempt standard pdf reading if pypdf or PyPDF2 is available
            try:
                import pypdf
                reader = pypdf.PdfReader(file_path)
                for page in reader.pages:
                    t = page.extract_text()
                    if t: raw_text += t + "\n"
            except ImportError:
                # Fallback 2: Read raw text streams from PDF bytes
                try:
                    with open(file_path, 'rb') as f:
                        content = f.read().decode('latin1', errors='ignore')
                        # Extract strings within text objects (BT ... ET)
                        matches = re.findall(r"\(([^)]+)\)\s*Tj", content)
                        if matches:
                            raw_text = " ".join(matches)
                except Exception:
                    pass

            return cls.extract_from_text(raw_text, source_file_path=file_path, file_type="PDF")

        # Image formats (JPG, PNG)
        elif ext in [".jpg", ".jpeg", ".png"]:
            raw_text = ""
            # Hook for pytesseract or Windows OCR when installed
            try:
                import pytesseract
                from PIL import Image
                img = Image.open(file_path)
                raw_text = pytesseract.image_to_string(img)
            except ImportError:
                raw_text = ""  # If OCR engine is not installed, raw text remains blank triggering review

            return cls.extract_from_text(
                raw_text,
                source_file_path=file_path,
                file_type=ext.replace(".", "").upper()
            )

        else:
            raise ValueError(f"Unsupported file format for laboratory report: {ext}. Expected PDF, JPG, or PNG.")

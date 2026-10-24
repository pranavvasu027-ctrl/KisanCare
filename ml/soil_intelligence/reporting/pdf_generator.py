"""
Pure-Python PDF Generator for KISANcare Soil Intelligence
=========================================================
Generates fully compliant ISO 32000 / PDF 1.4 documents without any external pip dependencies.
Renders structured multi-page soil intelligence reports with:
  - Header brand banner and privacy-masked metadata.
  - Formatted tables with column alignment and alternating row shading.
  - Color-coded alert boxes for INSUFFICIENT_DATA and human review flags.
  - Multi-year chronological management ledger.
  - Separate mass-balance ledger (strictly isolated from soil test concentration).
  - Uncalibrated heuristic uncertainty decomposition.
  - Actionable agronomic next steps and certified retesting protocols.
  - Running headers, footers, and page numbers ("Page X of Y").
"""

from typing import List, Dict, Tuple, Optional, Any
import io
import re

from ml.soil_intelligence.reporting.report_builder import (
    SoilReportViewModel,
    MeasuredParameterRow,
    ChronologicalEventRow
)


# Standard A4 Dimensions in Points (72 points = 1 inch)
PAGE_WIDTH: float = 595.28
PAGE_HEIGHT: float = 841.89
MARGIN_LEFT: float = 36.0
MARGIN_RIGHT: float = 36.0
MARGIN_TOP: float = 40.0
MARGIN_BOTTOM: float = 45.0
USABLE_WIDTH: float = PAGE_WIDTH - MARGIN_LEFT - MARGIN_RIGHT  # ~523.28 pt


def _escape_pdf_text(text: Any) -> str:
    """Escapes special characters and maps Unicode characters to WinAnsi/ASCII equivalents."""
    if text is None:
        return ""
    s = str(text)
    # Map common scientific Unicode symbols to clean ASCII equivalents
    replacements = {
        "²": "2", "₃": "3", "₄": "4", "₁": "1", "₂": "2",
        "±": "+/-", "°": " deg ", "×": "x", "—": " - ", "–": "-",
        "“": '"', "”": '"', "‘": "'", "’": "'", "≤": "<=", "≥": ">=",
        "½": "1/2", "¼": "1/4", "µ": "u", "•": "*"
    }
    for orig, repl in replacements.items():
        s = s.replace(orig, repl)
    # Retain standard ASCII characters (32 to 126)
    s = "".join(ch if 32 <= ord(ch) <= 126 else "?" for ch in s)
    # Escape PDF parentheses and backslashes
    s = s.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")
    return s


class PDFPageCanvas:
    """Maintains PDF graphics and text commands for a single page."""

    def __init__(self, page_number: int):
        self.page_number = page_number
        self.commands: List[str] = []

    def set_fill_color(self, r: float, g: float, b: float):
        self.commands.append(f"{r:.3f} {g:.3f} {b:.3f} rg")

    def set_stroke_color(self, r: float, g: float, b: float):
        self.commands.append(f"{r:.3f} {g:.3f} {b:.3f} RG")

    def set_line_width(self, w: float):
        self.commands.append(f"{w:.2f} w")

    def draw_rect(self, x: float, y: float, w: float, h: float, fill: bool = True, stroke: bool = False):
        op = "B" if (fill and stroke) else ("f" if fill else "s")
        self.commands.append(f"{x:.2f} {y:.2f} {w:.2f} {h:.2f} re {op}")

    def draw_line(self, x1: float, y1: float, x2: float, y2: float):
        self.commands.append(f"{x1:.2f} {y1:.2f} m {x2:.2f} {y2:.2f} l S")

    def draw_text(self, x: float, y: float, text: str, font: str = "/F1", size: float = 10.0, r: float = 0.0, g: float = 0.0, b: float = 0.0):
        escaped = _escape_pdf_text(text)
        self.commands.append("q")
        self.commands.append(f"{r:.3f} {g:.3f} {b:.3f} rg")
        self.commands.append("BT")
        self.commands.append(f"{font} {size:.2f} Tf")
        self.commands.append(f"{x:.2f} {y:.2f} Td")
        self.commands.append(f"({escaped}) Tj")
        self.commands.append("ET")
        self.commands.append("Q")

    def to_stream(self) -> bytes:
        content = "\n".join(self.commands) + "\n"
        return content.encode("latin1", errors="replace")


class SoilIntelligencePDFGenerator:
    """
    Renders a SoilReportViewModel into a complete, standalone PDF document.
    """

    def __init__(self):
        self.pages: List[PDFPageCanvas] = []
        self.current_page: Optional[PDFPageCanvas] = None
        self.cursor_y: float = 0.0

    def _new_page(self) -> PDFPageCanvas:
        page_num = len(self.pages) + 1
        page = PDFPageCanvas(page_num)
        self.pages.append(page)
        self.current_page = page
        self.cursor_y = PAGE_HEIGHT - MARGIN_TOP
        return page

    def _ensure_vertical_space(self, needed_pt: float):
        """Creates a new page if remaining vertical space is insufficient."""
        if self.cursor_y - needed_pt < MARGIN_BOTTOM:
            self._new_page()

    def generate_pdf_bytes(self, view_model: SoilReportViewModel) -> bytes:
        """
        Main layout orchestration. Returns raw PDF file bytes.
        """
        self.pages = []
        self._new_page()

        # 1. Document Header & Title Banner
        self._render_header_banner(view_model)

        # 2. Key Metadata & Identification Grid
        self._render_metadata_grid(view_model)

        # 3. Alert / Abstention Status Banner
        self._render_status_banner(view_model)

        # 4. Measured Laboratory Baseline Parameters (Section 1)
        self._render_measured_parameters(view_model)

        # 5. Multi-Year Management Chronology (Section 2)
        self._render_chronological_ledger(view_model)

        # 6. Cumulative Mass-Balance Ledger (Section 3 - Bookkeeping ONLY)
        self._render_mass_balance_ledger(view_model)

        # 7. Uncertainty Decomposition & Limitations (Section 4)
        self._render_uncertainty_section(view_model)

        # 8. Prediction Status & Safe Abstention Explanations (Section 5)
        self._render_abstention_explanation(view_model)

        # 9. Agronomic Advisory & Retesting Protocols (Section 6)
        self._render_advisory_section(view_model)

        # 10. Running Headers & Footers across all generated pages
        total_pages = len(self.pages)
        for page in self.pages:
            self._render_page_footer(page, total_pages, view_model.report_id)

        return self._assemble_pdf_document()

    # -----------------------------------------------------------------
    # Layout Component Renderers
    # -----------------------------------------------------------------

    def _render_header_banner(self, vm: SoilReportViewModel):
        page = self.current_page
        y = self.cursor_y

        # Forest green brand banner
        page.set_fill_color(0.12, 0.42, 0.22)
        page.draw_rect(MARGIN_LEFT, y - 48, USABLE_WIDTH, 48, fill=True, stroke=False)

        # White title text
        page.draw_text(MARGIN_LEFT + 12, y - 22, "KISANcare Soil Intelligence Report", font="/F2", size=16.0, r=1.0, g=1.0, b=1.0)
        page.draw_text(MARGIN_LEFT + 12, y - 38, "Multi-Year Dynamic Nutrient Tracking & Calibrated Lab Ingestion V1", font="/F1", size=9.5, r=0.9, g=0.95, b=0.9)

        # Report ID & Generation Timestamp (Right-aligned text block)
        page.draw_text(MARGIN_LEFT + USABLE_WIDTH - 150, y - 20, f"Report ID: {vm.report_id[:16]}...", font="/F2", size=8.0, r=1.0, g=1.0, b=1.0)
        page.draw_text(MARGIN_LEFT + USABLE_WIDTH - 150, y - 34, f"Generated: {vm.generation_date}", font="/F1", size=8.0, r=0.9, g=0.95, b=0.9)

        self.cursor_y -= 58

    def _render_metadata_grid(self, vm: SoilReportViewModel):
        page = self.current_page
        y = self.cursor_y

        # Light gray background container
        page.set_fill_color(0.96, 0.97, 0.98)
        page.set_stroke_color(0.82, 0.86, 0.90)
        page.set_line_width(0.75)
        page.draw_rect(MARGIN_LEFT, y - 42, USABLE_WIDTH, 42, fill=True, stroke=True)

        # Column 1: Plot & Farm (Masked)
        page.draw_text(MARGIN_LEFT + 8, y - 14, "Plot Identifier:", font="/F2", size=8.5, r=0.3, g=0.3, b=0.3)
        page.draw_text(MARGIN_LEFT + 80, y - 14, vm.plot_id_display, font="/F2", size=8.5, r=0.1, g=0.1, b=0.1)

        page.draw_text(MARGIN_LEFT + 8, y - 28, "Farm Account:", font="/F2", size=8.5, r=0.3, g=0.3, b=0.3)
        page.draw_text(MARGIN_LEFT + 80, y - 28, vm.farm_id_display, font="/F1", size=8.5, r=0.2, g=0.2, b=0.2)

        # Column 2: Location
        page.draw_text(MARGIN_LEFT + 200, y - 14, "Region:", font="/F2", size=8.5, r=0.3, g=0.3, b=0.3)
        page.draw_text(MARGIN_LEFT + 245, y - 14, vm.location_summary, font="/F1", size=8.5, r=0.2, g=0.2, b=0.2)

        page.draw_text(MARGIN_LEFT + 200, y - 28, "Privacy Scope:", font="/F2", size=8.5, r=0.3, g=0.3, b=0.3)
        page.draw_text(MARGIN_LEFT + 270, y - 28, "Masked / Confidential", font="/F1", size=8.5, r=0.4, g=0.4, b=0.4)

        # Column 3: Baseline Lab Date
        page.draw_text(MARGIN_LEFT + 375, y - 14, "Baseline Test:", font="/F2", size=8.5, r=0.3, g=0.3, b=0.3)
        page.draw_text(MARGIN_LEFT + 440, y - 14, vm.lab_sample_date, font="/F2", size=8.5, r=0.1, g=0.3, b=0.6)

        page.draw_text(MARGIN_LEFT + 375, y - 28, "Testing Lab:", font="/F2", size=8.5, r=0.3, g=0.3, b=0.3)
        lab_disp = (vm.lab_name[:24] + "..") if len(vm.lab_name) > 26 else vm.lab_name
        page.draw_text(MARGIN_LEFT + 435, y - 28, lab_disp, font="/F1", size=7.5, r=0.2, g=0.2, b=0.2)

        self.cursor_y -= 48

    def _render_status_banner(self, vm: SoilReportViewModel):
        self._ensure_vertical_space(32)
        page = self.current_page
        y = self.cursor_y

        is_insufficient = (vm.overall_status == "INSUFFICIENT_DATA")

        if is_insufficient:
            # Orange/Amber warning box for safe abstention
            page.set_fill_color(0.99, 0.95, 0.88)
            page.set_stroke_color(0.85, 0.55, 0.15)
            page.set_line_width(1.0)
            page.draw_rect(MARGIN_LEFT, y - 26, USABLE_WIDTH, 26, fill=True, stroke=True)

            page.draw_text(MARGIN_LEFT + 10, y - 11, "STATUS: INSUFFICIENT DATA / PREDICTION GATED", font="/F2", size=9.0, r=0.75, g=0.35, b=0.0)
            page.draw_text(MARGIN_LEFT + 10, y - 22, "Physical laboratory baseline and farm ledger displayed below. Empirical future prediction is abstained.", font="/F1", size=8.0, r=0.4, g=0.3, b=0.1)
        else:
            # Blue info box
            page.set_fill_color(0.92, 0.96, 0.99)
            page.set_stroke_color(0.20, 0.50, 0.80)
            page.set_line_width(1.0)
            page.draw_rect(MARGIN_LEFT, y - 26, USABLE_WIDTH, 26, fill=True, stroke=True)

            page.draw_text(MARGIN_LEFT + 10, y - 11, f"STATUS: {vm.overall_status}", font="/F2", size=9.0, r=0.1, g=0.3, b=0.7)
            page.draw_text(MARGIN_LEFT + 10, y - 22, "Verified laboratory records and multi-year management ledger.", font="/F1", size=8.0, r=0.2, g=0.3, b=0.5)

        self.cursor_y -= 34

    def _render_section_heading(self, title: str, subtitle: Optional[str] = None):
        self._ensure_vertical_space(28)
        page = self.current_page
        y = self.cursor_y

        # Underline bar
        page.set_fill_color(0.12, 0.42, 0.22)
        page.draw_rect(MARGIN_LEFT, y - 14, 4, 14, fill=True, stroke=False)

        page.draw_text(MARGIN_LEFT + 8, y - 11, title, font="/F2", size=10.5, r=0.12, g=0.42, b=0.22)
        if subtitle:
            page.draw_text(MARGIN_LEFT + 12 + (len(title)*6.5), y - 11, f"({subtitle})", font="/F3", size=8.5, r=0.4, g=0.4, b=0.4)

        page.set_stroke_color(0.85, 0.88, 0.90)
        page.set_line_width(0.5)
        page.draw_line(MARGIN_LEFT, y - 17, MARGIN_LEFT + USABLE_WIDTH, y - 17)

        self.cursor_y -= 22

    def _render_measured_parameters(self, vm: SoilReportViewModel):
        self._render_section_heading("1. Laboratory Baseline Soil Measurements", "PROVENANCE: MEASURED")
        page = self.current_page

        if not vm.has_lab_baseline or not vm.measured_parameters:
            self._ensure_vertical_space(30)
            page.draw_rect(MARGIN_LEFT, self.cursor_y - 25, USABLE_WIDTH, 25, fill=True, stroke=False)
            page.draw_text(MARGIN_LEFT + 10, self.cursor_y - 16, "NO PHYSICAL LABORATORY REPORT ON RECORD FOR THIS PLOT", font="/F2", size=9.0, r=0.8, g=0.2, b=0.1)
            self.cursor_y -= 32
            return

        # Laboratory metadata and accreditation status badge (D-01)
        self._ensure_vertical_space(20)
        lab_title_str = f"Lab: {vm.lab_name[:35]} | Date: {vm.lab_sample_date}"
        if vm.lab_certificate_no and vm.lab_certificate_no != "None":
            lab_title_str += f" | Certificate: {vm.lab_certificate_no}"

        self.current_page.draw_text(MARGIN_LEFT, self.cursor_y - 10, lab_title_str, font="/F2", size=7.5, r=0.2, g=0.2, b=0.2)
        self.cursor_y -= 14

        self._ensure_vertical_space(16)
        if getattr(vm, 'accreditation_verified', False):
            self.current_page.set_fill_color(0.92, 0.98, 0.93)
            self.current_page.draw_rect(MARGIN_LEFT, self.cursor_y - 12, USABLE_WIDTH, 12, fill=True, stroke=False)
            self.current_page.draw_text(
                MARGIN_LEFT + 6, self.cursor_y - 9,
                f"[ACCREDITATION: VERIFIED - {vm.accreditation_status_label}]",
                font="/F2", size=7.0, r=0.1, g=0.5, b=0.2
            )
        else:
            self.current_page.set_fill_color(0.98, 0.97, 0.92)
            self.current_page.draw_rect(MARGIN_LEFT, self.cursor_y - 12, USABLE_WIDTH, 12, fill=True, stroke=False)
            self.current_page.draw_text(
                MARGIN_LEFT + 6, self.cursor_y - 9,
                f"[ACCREDITATION: UNVERIFIED - {vm.accreditation_status_label}]",
                font="/F2", size=7.0, r=0.6, g=0.4, b=0.0
            )
        self.cursor_y -= 16

        # Render Review Flags if present
        if vm.lab_review_required and vm.lab_review_flags:
            for flag in vm.lab_review_flags:
                self._ensure_vertical_space(18)
                self.current_page.set_fill_color(0.99, 0.92, 0.92)
                self.current_page.draw_rect(MARGIN_LEFT, self.cursor_y - 14, USABLE_WIDTH, 14, fill=True, stroke=False)
                self.current_page.draw_text(MARGIN_LEFT + 6, self.cursor_y - 10, f"! {flag}", font="/F2", size=7.5, r=0.75, g=0.1, b=0.1)
                self.cursor_y -= 16

        # Table Column Widths: Parameter(120), Reading(95), Method(110), Normalized(100), Tier(98)
        col_w = [120.0, 95.0, 110.0, 100.0, 98.28]
        col_x = [MARGIN_LEFT]
        for w in col_w[:-1]:
            col_x.append(col_x[-1] + w)

        # Table Header
        self._ensure_vertical_space(18)
        page = self.current_page
        page.set_fill_color(0.20, 0.28, 0.36)
        page.draw_rect(MARGIN_LEFT, self.cursor_y - 14, USABLE_WIDTH, 14, fill=True, stroke=False)

        headers = ["Soil Parameter", "Verbatim Reading", "Extraction Protocol", "Normalized Elemental", "Fertility Classification"]
        for i, h in enumerate(headers):
            page.draw_text(col_x[i] + 4, self.cursor_y - 10, h, font="/F2", size=7.5, r=1.0, g=1.0, b=1.0)
        self.cursor_y -= 15

        # Table Rows
        for idx, row in enumerate(vm.measured_parameters):
            self._ensure_vertical_space(16)
            page = self.current_page

            # Alternating row shading
            bg_r, bg_g, bg_b = (0.97, 0.98, 0.99) if idx % 2 == 1 else (1.0, 1.0, 1.0)
            page.set_fill_color(bg_r, bg_g, bg_b)
            page.draw_rect(MARGIN_LEFT, self.cursor_y - 14, USABLE_WIDTH, 14, fill=True, stroke=False)

            # Draw cells
            page.draw_text(col_x[0] + 4, self.cursor_y - 10, row.parameter[:24], font="/F2", size=7.5, r=0.1, g=0.1, b=0.1)
            page.draw_text(col_x[1] + 4, self.cursor_y - 10, row.reported_reading[:20], font="/F1", size=7.5, r=0.2, g=0.2, b=0.2)
            page.draw_text(col_x[2] + 4, self.cursor_y - 10, row.reported_method[:24], font="/F1", size=7.0, r=0.3, g=0.3, b=0.3)
            page.draw_text(col_x[3] + 4, self.cursor_y - 10, row.normalized_elemental[:20], font="/F2", size=7.5, r=0.1, g=0.3, b=0.6)
            page.draw_text(col_x[4] + 4, self.cursor_y - 10, row.fertility_tier[:20], font="/F1", size=7.5, r=0.2, g=0.2, b=0.2)

            # Bottom cell border
            page.set_stroke_color(0.90, 0.92, 0.94)
            page.set_line_width(0.5)
            page.draw_line(MARGIN_LEFT, self.cursor_y - 14, MARGIN_LEFT + USABLE_WIDTH, self.cursor_y - 14)

            self.cursor_y -= 15

        self.cursor_y -= 8

    def _render_chronological_ledger(self, vm: SoilReportViewModel):
        self._render_section_heading("2. Chronological Multi-Year Farm Management History", "PROVENANCE: FARMER_RECORDED")
        page = self.current_page

        if not vm.timeline_events:
            self._ensure_vertical_space(20)
            page.draw_text(MARGIN_LEFT + 8, self.cursor_y - 12, "No intervening crop harvests or fertilizer applications recorded between test dates.", font="/F3", size=8.0, r=0.5, g=0.5, b=0.5)
            self.cursor_y -= 20
            return

        # Table Column Widths: Date(65), Type(85), Description(200), Delta N(58), Delta P(58), Delta K(57.28)
        col_w = [65.0, 85.0, 200.0, 58.0, 58.0, 57.28]
        col_x = [MARGIN_LEFT]
        for w in col_w[:-1]:
            col_x.append(col_x[-1] + w)

        self._ensure_vertical_space(16)
        page.set_fill_color(0.20, 0.28, 0.36)
        page.draw_rect(MARGIN_LEFT, self.cursor_y - 14, USABLE_WIDTH, 14, fill=True, stroke=False)
        headers = ["Date", "Event Category", "Agronomic Activity", "Delta N", "Delta P", "Delta K"]
        for i, h in enumerate(headers):
            page.draw_text(col_x[i] + 4, self.cursor_y - 10, h, font="/F2", size=7.5, r=1.0, g=1.0, b=1.0)
        self.cursor_y -= 15

        for idx, ev in enumerate(vm.timeline_events):
            self._ensure_vertical_space(15)
            page = self.current_page
            bg_r, bg_g, bg_b = (0.97, 0.98, 0.99) if idx % 2 == 1 else (1.0, 1.0, 1.0)
            page.set_fill_color(bg_r, bg_g, bg_b)
            page.draw_rect(MARGIN_LEFT, self.cursor_y - 13, USABLE_WIDTH, 13, fill=True, stroke=False)

            page.draw_text(col_x[0] + 4, self.cursor_y - 10, ev.event_date, font="/F1", size=7.5, r=0.1, g=0.1, b=0.1)
            page.draw_text(col_x[1] + 4, self.cursor_y - 10, ev.event_type[:16], font="/F2", size=7.5, r=0.2, g=0.3, b=0.4)
            page.draw_text(col_x[2] + 4, self.cursor_y - 10, ev.description[:44], font="/F1", size=7.5, r=0.2, g=0.2, b=0.2)
            page.draw_text(col_x[3] + 4, self.cursor_y - 10, ev.delta_n_kg_ha, font="/F2" if "+" in ev.delta_n_kg_ha else "/F1", size=7.5, r=0.1, g=0.4, b=0.1 if "+" in ev.delta_n_kg_ha else 0.7)
            page.draw_text(col_x[4] + 4, self.cursor_y - 10, ev.delta_p_kg_ha, font="/F2" if "+" in ev.delta_p_kg_ha else "/F1", size=7.5, r=0.1, g=0.4, b=0.1 if "+" in ev.delta_p_kg_ha else 0.7)
            page.draw_text(col_x[5] + 4, self.cursor_y - 10, ev.delta_k_kg_ha, font="/F2" if "+" in ev.delta_k_kg_ha else "/F1", size=7.5, r=0.1, g=0.4, b=0.1 if "+" in ev.delta_k_kg_ha else 0.7)

            page.set_stroke_color(0.90, 0.92, 0.94)
            page.set_line_width(0.5)
            page.draw_line(MARGIN_LEFT, self.cursor_y - 13, MARGIN_LEFT + USABLE_WIDTH, self.cursor_y - 13)
            self.cursor_y -= 14

        self.cursor_y -= 8

    def _render_mass_balance_ledger(self, vm: SoilReportViewModel):
        self._render_section_heading("3. Cumulative Agronomic Mass-Balance Ledger", "BOOKKEEPING ONLY")
        self._ensure_vertical_space(60)
        page = self.current_page
        y = self.cursor_y

        # Container
        page.set_fill_color(0.98, 0.99, 1.0)
        page.set_stroke_color(0.80, 0.85, 0.90)
        page.set_line_width(0.75)
        page.draw_rect(MARGIN_LEFT, y - 56, USABLE_WIDTH, 56, fill=True, stroke=True)

        # 3 Column summary for N, P, K
        nutrients = [("Nitrogen (N)", "N", 0), ("Phosphorus (P)", "P", 1), ("Potassium (K)", "K", 2)]
        col_w = USABLE_WIDTH / 3.0

        for name, key, idx in nutrients:
            cx = MARGIN_LEFT + (idx * col_w)
            add = vm.gross_additions.get(key, 0.0)
            rem = vm.gross_removals.get(key, 0.0)
            net = vm.net_balance.get(key, 0.0)
            unc = vm.balance_uncertainty.get(key, 0.0)

            page.draw_text(cx + 10, y - 12, name, font="/F2", size=8.5, r=0.15, g=0.25, b=0.35)
            page.draw_text(cx + 10, y - 24, f"Additions: +{add:.1f} kg/ha", font="/F1", size=7.5, r=0.1, g=0.5, b=0.1)
            page.draw_text(cx + 10, y - 35, f"Removals:  -{rem:.1f} kg/ha", font="/F1", size=7.5, r=0.7, g=0.1, b=0.1)
            net_str = f"Net Flux:  {net:+.1f} (+/- {unc:.1f}) kg/ha"
            page.draw_text(cx + 10, y - 48, net_str, font="/F2", size=8.0, r=0.1, g=0.1, b=0.1)

            if idx < 2:
                page.set_stroke_color(0.85, 0.88, 0.90)
                page.set_line_width(0.5)
                page.draw_line(cx + col_w, y - 6, cx + col_w, y - 50)

        self.cursor_y -= 62

        # Mandatory distinction warning banner
        self._ensure_vertical_space(20)
        page = self.current_page
        page.draw_text(
            MARGIN_LEFT + 6, self.cursor_y - 10,
            "CRITICAL NOTE: Net mass-balance represents field surface flux. It DOES NOT equal extractable soil available NPK.",
            font="/F2", size=7.5, r=0.8, g=0.2, b=0.1
        )
        self.cursor_y -= 16

        # Render Data Quality Flags (e.g. gaps, unrecorded crops)
        if vm.data_quality_flags:
            for flag in vm.data_quality_flags:
                self._ensure_vertical_space(14)
                page = self.current_page
                page.draw_text(
                    MARGIN_LEFT + 6, self.cursor_y - 10,
                    f"! Data Quality Notice: {flag[:100]}",
                    font="/F2", size=7.0, r=0.75, g=0.2, b=0.1
                )
                self.cursor_y -= 13

    def _render_uncertainty_section(self, vm: SoilReportViewModel):
        self._render_section_heading("4. Uncertainty Decomposition & Limitations", "STATUS: UNCALIBRATED_HEURISTIC_BOUND")
        self._ensure_vertical_space(42)
        page = self.current_page
        y = self.cursor_y

        page.set_fill_color(0.97, 0.97, 0.97)
        page.set_stroke_color(0.85, 0.85, 0.85)
        page.set_line_width(0.5)
        page.draw_rect(MARGIN_LEFT, y - 36, USABLE_WIDTH, 36, fill=True, stroke=True)

        n_unc = vm.uncertainty_bounds.get("N", 0.0)
        p_unc = vm.uncertainty_bounds.get("P", 0.0)
        k_unc = vm.uncertainty_bounds.get("K", 0.0)

        page.draw_text(MARGIN_LEFT + 10, y - 12, "Propagated Physical Uncertainty Bounds (Quadrate Combination):", font="/F2", size=8.0, r=0.2, g=0.2, b=0.2)
        page.draw_text(MARGIN_LEFT + 10, y - 24, f"Nitrogen: +/- {n_unc:.1f} kg N/ha   |   Phosphorus: +/- {p_unc:.1f} kg P/ha   |   Potassium: +/- {k_unc:.1f} kg K/ha", font="/F2", size=8.0, r=0.1, g=0.3, b=0.6)

        self.cursor_y -= 42

    def _render_abstention_explanation(self, vm: SoilReportViewModel):
        self._render_section_heading("5. Operational Prediction Gate & Safe Abstention Rationale")
        self._ensure_vertical_space(48)
        page = self.current_page
        y = self.cursor_y

        page.set_fill_color(0.99, 0.98, 0.95)
        page.set_stroke_color(0.90, 0.80, 0.65)
        page.set_line_width(0.75)
        page.draw_rect(MARGIN_LEFT, y - 44, USABLE_WIDTH, 44, fill=True, stroke=True)

        page.draw_text(MARGIN_LEFT + 8, y - 12, "Why is an empirical future NPK prediction not provided in this report?", font="/F2", size=8.5, r=0.6, g=0.3, b=0.0)

        reason_text = vm.abstain_reasons[0] if vm.abstain_reasons else "The genuine longitudinal ground-truth gate is BLOCKED."
        page.draw_text(MARGIN_LEFT + 8, y - 24, reason_text[:110], font="/F1", size=7.5, r=0.2, g=0.2, b=0.2)
        if len(reason_text) > 110:
            page.draw_text(MARGIN_LEFT + 8, y - 34, reason_text[110:220], font="/F1", size=7.5, r=0.2, g=0.2, b=0.2)

        self.cursor_y -= 52

    def _render_advisory_section(self, vm: SoilReportViewModel):
        self._render_section_heading("6. Practical Next Steps & Agronomic Recommendations")
        self._ensure_vertical_space(60)
        page = self.current_page

        for rec in vm.retesting_advice[:3]:
            self._ensure_vertical_space(14)
            page = self.current_page
            page.draw_text(MARGIN_LEFT + 6, self.cursor_y - 10, f"* {rec[:115]}", font="/F1", size=7.5, r=0.15, g=0.15, b=0.15)
            self.cursor_y -= 13

        # Retesting depth & agronomist notice box
        self._ensure_vertical_space(32)
        page = self.current_page
        page.set_fill_color(0.94, 0.97, 0.94)
        page.set_stroke_color(0.60, 0.80, 0.60)
        page.set_line_width(0.5)
        page.draw_rect(MARGIN_LEFT, self.cursor_y - 26, USABLE_WIDTH, 26, fill=True, stroke=True)

        page.draw_text(MARGIN_LEFT + 8, self.cursor_y - 10, f"Recommended Soil Retesting Depth: {vm.retesting_depth_cm}", font="/F2", size=8.0, r=0.1, g=0.4, b=0.1)
        page.draw_text(MARGIN_LEFT + 8, self.cursor_y - 20, vm.qualified_agronomist_notice[:115], font="/F3", size=7.0, r=0.2, g=0.3, b=0.2)

        self.cursor_y -= 34

    def _render_page_footer(self, page: PDFPageCanvas, total_pages: int, report_id: str):
        page.set_stroke_color(0.85, 0.88, 0.90)
        page.set_line_width(0.5)
        page.draw_line(MARGIN_LEFT, MARGIN_BOTTOM + 12, MARGIN_LEFT + USABLE_WIDTH, MARGIN_BOTTOM + 12)

        # Footer Left: Confidential Notice
        page.draw_text(MARGIN_LEFT, MARGIN_BOTTOM + 2, "KISANcare Soil Intelligence V1 | Confidential & Proprietary | Not an empirical prescription", font="/F1", size=7.0, r=0.5, g=0.5, b=0.5)

        # Footer Right: Page Number
        page_str = f"Page {page.page_number} of {total_pages}"
        page.draw_text(MARGIN_LEFT + USABLE_WIDTH - 55, MARGIN_BOTTOM + 2, page_str, font="/F2", size=7.5, r=0.4, g=0.4, b=0.4)

    # -----------------------------------------------------------------
    # ISO 32000 / PDF 1.4 Binary Serialization
    # -----------------------------------------------------------------

    def _assemble_pdf_document(self) -> bytes:
        """
        Assembles all PDF objects, streams, cross-reference tables, and trailer.
        """
        buf = io.BytesIO()
        buf.write(b"%PDF-1.4\n")
        buf.write(b"%\xe2\xe3\xcf\xd3\n")  # Binary marker comment

        offsets: List[int] = []

        def _record_obj() -> int:
            offsets.append(buf.tell())
            return len(offsets)

        num_pages = len(self.pages)

        # Object 1: Catalog
        _record_obj()
        buf.write(b"1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n")

        # Object 2: Pages Tree
        _record_obj()
        kids_str = " ".join(f"{7 + (i * 2)} 0 R" for i in range(num_pages))
        buf.write(f"2 0 obj\n<< /Type /Pages /Kids [{kids_str}] /Count {num_pages} >>\nendobj\n".encode("latin1"))

        # Object 3: Font Helvetica (/F1)
        _record_obj()
        buf.write(b"3 0 obj\n<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica /Encoding /WinAnsiEncoding >>\nendobj\n")

        # Object 4: Font Helvetica-Bold (/F2)
        _record_obj()
        buf.write(b"4 0 obj\n<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica-Bold /Encoding /WinAnsiEncoding >>\nendobj\n")

        # Object 5: Font Helvetica-Oblique (/F3)
        _record_obj()
        buf.write(b"5 0 obj\n<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica-Oblique /Encoding /WinAnsiEncoding >>\nendobj\n")

        # Object 6: Font Courier (/F4)
        _record_obj()
        buf.write(b"6 0 obj\n<< /Type /Font /Subtype /Type1 /BaseFont /Courier /Encoding /WinAnsiEncoding >>\nendobj\n")

        # Page and Stream Objects (pairs: 7 & 8, 9 & 10, ...)
        for i, page in enumerate(self.pages):
            page_obj_id = 7 + (i * 2)
            stream_obj_id = page_obj_id + 1

            stream_data = page.to_stream()

            # Page Object
            _record_obj()
            buf.write(
                f"{page_obj_id} 0 obj\n"
                f"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 {PAGE_WIDTH:.2f} {PAGE_HEIGHT:.2f}] "
                f"/Contents {stream_obj_id} 0 R "
                f"/Resources << /Font << /F1 3 0 R /F2 4 0 R /F3 5 0 R /F4 6 0 R >> >> >>\n"
                f"endobj\n".encode("latin1")
            )

            # Stream Object
            _record_obj()
            buf.write(
                f"{stream_obj_id} 0 obj\n"
                f"<< /Length {len(stream_data)} >>\n"
                f"stream\n".encode("latin1")
            )
            buf.write(stream_data)
            buf.write(b"endstream\nendobj\n")

        # Cross-reference table
        xref_offset = buf.tell()
        total_objs = len(offsets) + 1
        buf.write(f"xref\n0 {total_objs}\n".encode("latin1"))
        buf.write(b"0000000000 65535 f \n")
        for off in offsets:
            buf.write(f"{off:010d} 00000 n \n".encode("latin1"))

        # Trailer
        buf.write(
            f"trailer\n"
            f"<< /Size {total_objs} /Root 1 0 R >>\n"
            f"startxref\n"
            f"{xref_offset}\n"
            f"%%EOF\n".encode("latin1")
        )

        return buf.getvalue()

"""
ComicCraft - PDF Exporter
Compiles comic panels, illustrations, and narration into a professionally styled multi-page PDF using FPDF2.
"""

import logging
import os
import time
from pathlib import Path
from typing import Any, Dict, List
from fpdf import FPDF

logger = logging.getLogger("comiccraft.exporters")
logging.basicConfig(level=logging.INFO)

BASE_DIR = Path(__file__).resolve().parent.parent
EXPORTS_DIR = BASE_DIR / "static" / "exports"
EXPORTS_DIR.mkdir(parents=True, exist_ok=True)


class ComicPDF(FPDF):
    """Custom FPDF class styled for comic books with white theme aesthetics."""
    
    def __init__(self, comic_title="ComicCraft Strip"):
        super().__init__(orientation="P", unit="mm", format="A4")
        self.comic_title = comic_title
        self.set_auto_page_break(auto=True, margin=15)

    def header(self):
        # Only print header on non-cover pages
        if self.page_no() > 1:
            self.set_font("helvetica", "B", 9)
            self.set_text_color(100, 116, 139)
            self.cell(0, 8, f"ComicCraft AI Studio  |  {self.comic_title}", border=0, align="L")
            self.set_font("helvetica", "I", 9)
            self.cell(0, 8, f"Page {self.page_no()}", border=0, align="R", new_x="LMARGIN", new_y="NEXT")
            self.set_draw_color(226, 232, 240)
            self.set_line_width(0.4)
            self.line(10, 16, 200, 16)
            self.ln(4)

    def footer(self):
        self.set_y(-14)
        self.set_font("helvetica", "I", 8)
        self.set_text_color(148, 163, 184)
        self.cell(0, 8, "Generated with Gemini Models & ComicCraft Studio  *  comiccraft.ai", border=0, align="C")


def _sanitize_for_pdf(text: str) -> str:
    """Replaces non-latin or special unicode quotes/dashes with safe printable equivalents."""
    if not text:
        return ""
    replacements = {
        '\u2018': "'", '\u2019': "'",
        '\u201c': '"', '\u201d': '"',
        '\u2013': "-", '\u2014': "--",
        '\u2026': "...", '\u00a0': " ",
        '\u2022': "*", '\u2032': "'",
        '\u2033': '"',
    }
    for orig, repl in replacements.items():
        text = text.replace(orig, repl)
    # Filter to latin-1 encodable characters to ensure 100% crash-free PDF generation
    return "".join(c if ord(c) < 256 else "?" for c in text)


def save_pdf(
    layout: List[Dict[str, Any]],
    title: str = "ComicCraft Comic",
    author: str = "ComicCraft AI",
    character_name: str = "Hero",
    setting: str = "Unknown Realm",
    tone: str = "Dramatic",
    art_style: str = "Comic Book"
) -> str:
    """
    Compiles the full comic into a multi-page PDF file using FPDF.
    Each panel's image, title, scene description, and narration are placed neatly on separate pages.
    The final PDF is saved into static/exports with a timestamped filename.
    
    Returns:
        The relative web URL path to the saved PDF (e.g., '/static/exports/comic_123456.pdf').
    """
    timestamp = int(time.time())
    safe_title = "".join(c if c.isalnum() else "_" for c in title)[:25]
    pdf_filename = f"comic_{timestamp}_{safe_title}.pdf"
    pdf_path = EXPORTS_DIR / pdf_filename

    logger.info(f"Compiling comic PDF to {pdf_path}...")
    
    pdf = ComicPDF(comic_title=_sanitize_for_pdf(title))
    pdf.set_margins(15, 15, 15)

    # ================= COVER PAGE =================
    pdf.add_page()
    
    # Border frame on cover
    pdf.set_draw_color(15, 23, 42)
    pdf.set_line_width(1.2)
    pdf.rect(10, 10, 190, 277)
    pdf.set_line_width(0.3)
    pdf.set_draw_color(124, 58, 237)
    pdf.rect(12, 12, 186, 273)

    pdf.ln(25)
    
    # Studio badge
    pdf.set_fill_color(243, 232, 255)
    pdf.set_text_color(124, 58, 237)
    pdf.set_font("helvetica", "B", 10)
    pdf.cell(0, 10, "COMICCRAFT AI STUDIOS  |  ORIGINAL STORY", border=0, align="C", fill=True, new_x="LMARGIN", new_y="NEXT")
    pdf.ln(12)

    # Main Title
    pdf.set_font("helvetica", "B", 26)
    pdf.set_text_color(15, 23, 42)
    pdf.multi_cell(0, 12, _sanitize_for_pdf(title.upper()), border=0, align="C")
    pdf.ln(8)

    # Subtitle / Premise
    pdf.set_font("helvetica", "I", 12)
    pdf.set_text_color(100, 116, 139)
    pdf.cell(0, 8, f"An Illustrated 5-Panel Comic Adventure", border=0, align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(15)

    # Story Metadata Box
    pdf.set_fill_color(248, 250, 252)
    pdf.set_draw_color(203, 213, 225)
    pdf.set_line_width(0.5)
    
    meta_x, meta_y = 30, pdf.get_y()
    pdf.rect(meta_x, meta_y, 150, 68, style="FD")
    
    pdf.set_xy(meta_x + 8, meta_y + 8)
    pdf.set_font("helvetica", "B", 11)
    pdf.set_text_color(15, 23, 42)
    pdf.cell(40, 9, "PROTAGONIST:", border=0)
    pdf.set_font("helvetica", "", 11)
    pdf.cell(90, 9, _sanitize_for_pdf(character_name), border=0, new_x="LMARGIN", new_y="NEXT")
    
    pdf.set_x(meta_x + 8)
    pdf.set_font("helvetica", "B", 11)
    pdf.cell(40, 9, "SETTING:", border=0)
    pdf.set_font("helvetica", "", 11)
    pdf.cell(90, 9, _sanitize_for_pdf(setting), border=0, new_x="LMARGIN", new_y="NEXT")

    pdf.set_x(meta_x + 8)
    pdf.set_font("helvetica", "B", 11)
    pdf.cell(40, 9, "TONE:", border=0)
    pdf.set_font("helvetica", "", 11)
    pdf.cell(90, 9, _sanitize_for_pdf(tone), border=0, new_x="LMARGIN", new_y="NEXT")

    pdf.set_x(meta_x + 8)
    pdf.set_font("helvetica", "B", 11)
    pdf.cell(40, 9, "ART STYLE:", border=0)
    pdf.set_font("helvetica", "", 11)
    pdf.cell(90, 9, _sanitize_for_pdf(art_style), border=0, new_x="LMARGIN", new_y="NEXT")

    pdf.set_x(meta_x + 8)
    pdf.set_font("helvetica", "B", 11)
    pdf.cell(40, 9, "AI MODELS:", border=0)
    pdf.set_font("helvetica", "", 11)
    pdf.cell(90, 9, "Gemini Flash + Gemini Pro + Stable Diffusion", border=0, new_x="LMARGIN", new_y="NEXT")

    pdf.set_y(meta_y + 80)
    pdf.set_font("helvetica", "I", 10)
    pdf.set_text_color(148, 163, 184)
    pdf.cell(0, 8, "Turn the page to begin the journey...", border=0, align="C", new_x="LMARGIN", new_y="NEXT")

    # ================= CONSECUTIVE PAGES (1 PANEL PER PAGE) =================
    for panel in layout:
        pdf.add_page()
        
        p_num = panel.get("panel_number", 1)
        p_title = panel.get("title", f"Panel {p_num}")
        p_desc = panel.get("scene_description", "")
        p_caption = panel.get("caption", "")
        p_dialogue = panel.get("dialogue", "")
        p_narration = panel.get("narration", "")
        img_rel_path = panel.get("image_path", "")

        # Panel Header Banner
        pdf.set_fill_color(15, 23, 42)
        pdf.set_text_color(255, 255, 255)
        pdf.set_font("helvetica", "B", 13)
        header_text = _sanitize_for_pdf(f"PANEL {p_num} : {p_title.upper()}")
        pdf.cell(0, 11, f"   {header_text}", border=0, fill=True, new_x="LMARGIN", new_y="NEXT")
        pdf.ln(5)

        # Panel Illustration
        img_resolved = None
        if img_rel_path:
            clean_rel = img_rel_path.lstrip("/\\")
            cand1 = BASE_DIR / clean_rel
            cand2 = Path(img_rel_path)
            if cand1.exists():
                img_resolved = str(cand1)
            elif cand2.exists():
                img_resolved = str(cand2)

        if img_resolved and os.path.exists(img_resolved):
            # Centered image: 110mm x 110mm
            img_w = 115
            img_x = (210 - img_w) / 2
            curr_y = pdf.get_y()
            
            # Comic frame border around image
            pdf.set_draw_color(15, 23, 42)
            pdf.set_line_width(1.0)
            pdf.rect(img_x - 1, curr_y - 1, img_w + 2, img_w + 2)
            
            pdf.image(img_resolved, x=img_x, y=curr_y, w=img_w, h=img_w)
            pdf.set_y(curr_y + img_w + 6)
        else:
            pdf.ln(10)

        # Scene Setting Description (Italicized context)
        if p_desc:
            pdf.set_fill_color(248, 250, 252)
            pdf.set_draw_color(226, 232, 240)
            pdf.set_line_width(0.3)
            pdf.set_font("helvetica", "I", 9.5)
            pdf.set_text_color(71, 85, 105)
            pdf.multi_cell(0, 6, _sanitize_for_pdf(f"Scene: {p_desc}"), border=1, fill=True)
            pdf.ln(4)

        # Ambient Caption (Comic narrative caption box)
        if p_caption:
            pdf.set_fill_color(254, 249, 195)  # Light comic yellow
            pdf.set_draw_color(234, 179, 8)
            pdf.set_line_width(0.5)
            pdf.set_font("helvetica", "B", 9.5)
            pdf.set_text_color(113, 63, 18)
            pdf.multi_cell(0, 6, _sanitize_for_pdf(p_caption), border=1, fill=True)
            pdf.ln(3)

        # Narration & Dialogue Speech Bubble
        if p_dialogue or p_narration:
            pdf.set_fill_color(255, 255, 255)
            pdf.set_draw_color(124, 58, 237)
            pdf.set_line_width(0.6)
            
            if p_narration and p_narration != p_desc:
                pdf.set_font("helvetica", "", 10)
                pdf.set_text_color(30, 41, 59)
                pdf.multi_cell(0, 6, _sanitize_for_pdf(p_narration), border="L", fill=False)
                pdf.ln(2)

            if p_dialogue:
                pdf.set_font("helvetica", "B", 10.5)
                pdf.set_text_color(15, 23, 42)
                pdf.multi_cell(0, 6.5, _sanitize_for_pdf(p_dialogue), border=1, fill=True)
                pdf.ln(2)

    # Save PDF
    pdf.output(str(pdf_path))
    logger.info(f"PDF successfully exported to {pdf_path}")
    return f"/static/exports/{pdf_filename}"

"""
Utilities to build the final red-line PDF with optional watermarks / footnotes.
"""
from io import BytesIO
from typing import List, Optional
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from PyPDF2 import PdfReader, PdfWriter
from pathlib import Path

def build_redline_pdf(
    original_pdf: Path,
    clauses,  # List[Clause] Pydantic models
    include_ghosts: bool = True,
    include_eli5: bool = False,
    watermark: Optional[str] = None,
) -> bytes:
    """
    Returns bytes of the new PDF.
    For MVP we simply stamp coloured squares and optional watermark.
    A real implementation would use pdfplumber + strike-through + insert text.
    """
    reader = PdfReader(original_pdf)
    writer = PdfWriter()

    packet = BytesIO()
    can = canvas.Canvas(packet, pagesize=letter)

    if watermark:
        can.saveState()
        can.setFont("Helvetica", 60)
        can.setFillColorRGB(0.9, 0.9, 0.9)
        can.rotate(45)
        can.drawString(200, 0, watermark)
        can.restoreState()

    can.save()
    packet.seek(0)
    watermark_pdf = PdfReader(packet)
    watermark_page = watermark_pdf.pages[0]

    for page in reader.pages:
        page.merge_page(watermark_page)
        writer.add_page(page)

    # TODO: inject red/yellow/green annotations & ELI5 footnotes
    # for now we just merge the watermark

    out = BytesIO()
    writer.write(out)
    return out.getvalue()
"""
OCR placeholder – swap in AWS Textract, Azure, Google, etc. if needed.
easyocr is used here because it is pip-installable and offline-capable.
"""
import easyocr
import asyncio
from typing import List
from pathlib import Path

# singleton reader (lazy-loaded)
_reader = None

def _get_reader() -> easyocr.Reader:
    global _reader
    if _reader is None:
        _reader = easyocr.Reader(["en"], gpu=False)
    return _reader

async def ocr_pdf_or_image(file_path: Path) -> str:
    """
    Returns plain UTF-8 text extracted from PDF or image.
    For PDF we simply rasterise page-1 → png → OCR.
    """
    loop = asyncio.get_event_loop()
    reader = _get_reader()

    # naive: if pdf → convert page 1 to png via pdf2image (needs poppler)
    if file_path.suffix.lower() == ".pdf":
        try:
            from pdf2image import convert_from_path
            images = convert_from_path(file_path, dpi=200, first_page=1, last_page=1)
            img = images[0]
        except Exception:
            # fallback: pretend we got nothing
            return ""
    else:
        from PIL import Image
        img = Image.open(file_path)

    # run blocking OCR in thread-pool
    bounds = await loop.run_in_executor(None, reader.readtext, img)
    text = " ".join([b[1] for b in bounds])
    return text
from fastapi import FastAPI, File, Form, UploadFile, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import pdfplumber, docx, easyocr, io, os, uuid
from typing import List

app = FastAPI(title="Doc & Image Reader")

# Jinja templates
templates = Jinja2Templates(directory="templates")

reader = None
def get_ocr():
    global reader
    if reader is None:
        reader = easyocr.Reader(['en'])  
    return reader

def ocr_image_bytes(file_bytes: bytes) -> str:
    ocr = get_ocr()
    result = ocr.readtext(file_bytes, detail=0)
    return "\n".join(result)

def extract_doc_text(file_bytes: bytes, filename: str) -> str:
    text = ""
    if filename.lower().endswith(".pdf"):
        with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
            text = "\n".join(page.extract_text() or "" for page in pdf.pages)
    elif filename.lower().endswith(".docx"):
        doc = docx.Document(io.BytesIO(file_bytes))
        text = "\n".join(p.text for p in doc.paragraphs)
    else:  # plain txt
        text = file_bytes.decode("utf-8", errors="ignore")
    return text

@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/upload")
async def upload(
    document: UploadFile = File(None),
    images: List[UploadFile] = File(None)
):
    """
    Accept either:
      - single document (PDF/DOCX/TXT) via 'document' form field
      - multiple images via 'images' form field
    Returns JSON { "text": "<full extracted text>" }
    """
    full_text = []

    if document and document.filename:
        contents = await document.read()
        full_text.append(extract_doc_text(contents, document.filename))

    if images:
        for img in images:
            if not img.filename:
                continue
            contents = await img.read()
            full_text.append(ocr_image_bytes(contents))

    concatenated = "\n\n".join(full_text).strip()
    return {"text": concatenated}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)
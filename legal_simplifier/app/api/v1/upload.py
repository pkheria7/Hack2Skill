from fastapi import APIRouter, UploadFile, File, Form
from typing import List
import uuid, json
from app.models import UploadResp

router = APIRouter()

@router.post("/upload", response_model=UploadResp)
async def upload_files(
    files: List[UploadFile] = File(...),
    doc_name: str = Form(...),
    doc_type: str = Form("nda"),
):
    uid = str(uuid.uuid4())
    # TODO: save files, trigger OCR async job
    return UploadResp(uid=uid, status="queued", message="OCR started")
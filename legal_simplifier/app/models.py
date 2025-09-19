from pydantic import BaseModel, Field
from typing import List, Optional, Literal

class UploadReq(BaseModel):
    doc_name: str
    doc_type: Literal["nda", "msa", "other"] = "nda"

class UploadResp(BaseModel):
    uid: str
    status: Literal["queued", "completed"]
    message: Optional[str] = None

class Clause(BaseModel):
    id: int
    original_text: str
    risk: Literal["red", "yellow", "green", "ghost"]
    type: str
    eli5: str
    suggested_text: Optional[str] = None
    start_idx: Optional[int] = None
    end_idx: Optional[int] = None

class ResultResp(BaseModel):
    uid: str
    name: str
    status: str
    parties: Optional[List[str]] = None
    clauses: List[Clause]
    ghost_clauses: List[Clause] = Field(default_factory=list)



class ClauseDetail(BaseModel):
    clause_id: int
    original_text: str
    risk: Literal["red", "yellow", "green", "ghost"]
    eli5: str
    rewrite_options: List[str]
    legal_aids: List[dict]
    video_script: dict
    banner: Optional[str] = None

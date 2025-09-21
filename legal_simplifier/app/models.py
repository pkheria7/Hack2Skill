from pydantic import BaseModel, Field
from typing import List, Optional, Literal, Dict, Union

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


# Extended models for chatbot
class ClauseDetail(BaseModel):
    clause_id: int
    original_text: str
    risk: str
    eli5: str
    rewrite_options: List[str]
    ai_response: str
    risk_after: str
    next_actions: List[str]
    legal_aids: List[Dict[str, str]]
    video_script: Dict[str, Union[str, List[str]]]
    banner: Optional[str] = None

class ChatRequest(BaseModel):
    uid: str
    question: str
    session_id: Optional[str] = None

from pydantic import BaseModel
from typing import List

class NegotiateRequest(BaseModel):
    uid: str                      # unique document/session id
    clause_id: int                # which clause is being negotiated
    option: str                   # stance: "friendly", "firm", "aggressive"
    current_risk: str             # "red", "yellow", "green"
    original_clause: str           # full clause text being negotiated

class NegotiateResponse(BaseModel):
    clause_id: int
    option: str
    original_clause: str           # include original clause in response for context
    ai_explanation: str            # explanation of suggested changes
    counter_statements: List[str]  # AI-generated safer/better alternatives
    risk_after: str                # updated risk level after negotiation
    next_actions: List[str]        # possible next actions: Accept / Counter / Ask lawyer



     

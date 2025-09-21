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
    uid: str                        # user id
    clauseId: int                   # clause id
    tone: str                       # friendly / firm / aggressive
    origin: str                     # original clause text
    risk: str              # current risk level of the clause (red, yellow, green)

class NegotiateResponse(BaseModel):
    rewritten_clause: str          # include original clause in response for context
    ai_explanation: str            # explanation of suggested changes # AI-generated safer/better alternatives
    risk_after: str                # updated risk level after negotiation        # possible next actions: Accept / Counter / Ask lawyer



     

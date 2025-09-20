import os
import json
import re
from fastapi import APIRouter, HTTPException
from app.models import ClauseDetail
from app.config import ask_groq

router = APIRouter(tags=["Clause Detail"])

def get_clause_store(uid: str, clause_id: int) -> str:
    """Fetch a clause text by UID and index from store/"""
    doc_dir = os.path.join("store", uid)
    if not os.path.exists(doc_dir):
        raise HTTPException(404, "document not found")

    files = sorted([f for f in os.listdir(doc_dir) if f.endswith(".txt")])
    if clause_id >= len(files):
        raise HTTPException(404, "clause not found")

    with open(os.path.join(doc_dir, files[clause_id]), "r", encoding="utf-8") as f:
        return f.read().strip()

@router.get("/clause/{uid}/{clause_id}", response_model=ClauseDetail)
def clause_detail(uid: str, clause_id: int):
    original_text = get_clause_store(uid, clause_id)

    # Strict prompt for Groq
    prompt = f"""
You are an expert legal assistant. Analyze the following contract clause.

STRICT INSTRUCTIONS:
- Output ONLY valid JSON.
- Evaluate clause risk.
- Provide an ELI5 explanation.
- Suggest rewrites that would make it safer.
- Simulate negotiation stance and predict AI counter-response.
- Suggest what the risk would be if the rewrite was applied.
- Suggest next actions the user could take.

Risk Rules:
- green = safe / fair
- yellow = caution
- red = risky / predatory

JSON format (strict):
{{
  "risk": "green|yellow|red",
  "eli5": "short simple explanation",
  "rewrite_options": ["better rewrite option 1", "better rewrite option 2"],
  "ai_response": "how the counterparty might reply",
  "risk_after": "green|yellow|red",
  "next_actions": ["Accept", "Counter", "Ask-human-lawyer"]
}}

Clause: {original_text}
"""



    try:
        ai_raw = ask_groq(prompt)

        # Extract only JSON block using regex
        match = re.search(r"\{.*\}", ai_raw, re.S)
        if match:
            ai_json = json.loads(match.group())
        else:
            raise ValueError("No JSON found in Groq response")

    except Exception:
        ai_json = {
            "risk": "yellow",
            "eli5": "Simplification unavailable",
            "rewrite_options": ["Rephrase needed"]
        }

    return ClauseDetail(
    clause_id=clause_id,
    original_text=original_text,
    risk=ai_json.get("risk", "yellow"),
    eli5=ai_json.get("eli5", "No explanation"),
    rewrite_options=ai_json.get("rewrite_options", []),
    ai_response=ai_json.get("ai_response", "No response generated"),
    risk_after=ai_json.get("risk_after", "yellow"),
    next_actions=ai_json.get("next_actions", ["Ask-human-lawyer"]),
    legal_aids=[
        {"name": "Community Law Centre", "type": "community", "url": "https://communitylaw.example"},
        {"name": "QuickCall Lawyer", "type": "private", "url": "https://quickcall.example"}
    ],
    video_script={
        "title": "Clause explainer",
        "script_lines": ["This clause sets rules between parties.", "Understand before signing."]
    },
    banner="🚨 Talk to a lawyer first" if ai_json.get("risk") == "red" else None
)


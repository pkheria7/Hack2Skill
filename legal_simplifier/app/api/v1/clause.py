# app/api/v1/clause.py
import json
from fastapi import APIRouter, HTTPException
from app.models import ClauseDetail
from app.services.llm_service import ask_groq
from app.services.storage import load_clauses

router = APIRouter()

@router.get("/clause/{uid}/{clause_id}", response_model=ClauseDetail)
async def get_clause(uid: str, clause_id: int):
    clauses = load_clauses(uid)

    if clause_id >= len(clauses):
        raise HTTPException(404, "clause not found")

    clause_text = clauses[clause_id]

    # 1. Rewrite options
    prompt_rewrite = (
        "Suggest 3 fair, plain-language rewrite alternatives for this contract clause. "
        "Reply ONLY JSON list of strings.\n\n"
        f"Clause: {clause_text}"
    )
    try:
        rewrite_options = json.loads(ask_groq(prompt_rewrite))
    except:
        rewrite_options = ["Each party pays its own legal costs."]

    # 2. Video script
    prompt_video = (
        "Create a 15-second explainer script for this clause in 2-3 short lines. "
        "Reply ONLY JSON: {\"title\":\"...\", \"script_lines\":[\"line1\",\"line2\"]}\n\n"
        f"Clause: {clause_text}"
    )
    try:
        video_script = json.loads(ask_groq(prompt_video))
    except:
        video_script = {
            "title": "Clause explainer",
            "script_lines": ["This clause sets rules between parties.", "Understand before signing."]
        }

    # 3. Placeholder risk + eli5 (later you can generate these in upload step)
    risk = "yellow" if "indemnify" in clause_text.lower() else "green"
    eli5 = "Simple explanation placeholder (to be AI-generated)."

    # 4. Static legal aids
    legal_aids = [
        {"name": "Community Law Centre", "type": "community", "url": "https://communitylaw.example"},
        {"name": "QuickCall Lawyer", "type": "private", "url": "https://quickcall.example"}
    ]

    # 5. Banner warnings
    banner = None
    if risk == "red":
        banner = "🚨 Talk to a lawyer first"
    elif risk == "yellow":
        banner = "⚠️ Consider asking for clarification"

    return ClauseDetail(
        clause_id=clause_id,
        original_text=clause_text,
        risk=risk,
        eli5=eli5,
        rewrite_options=rewrite_options,
        legal_aids=legal_aids,
        video_script=video_script,
        banner=banner
    )

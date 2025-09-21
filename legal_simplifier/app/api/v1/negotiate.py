from fastapi import APIRouter, HTTPException
from app.config import groq_client
from app.models import NegotiateRequest, NegotiateResponse
import json, re

router = APIRouter()

@router.post("/negotiate", response_model=NegotiateResponse)
async def negotiate_clause(payload: NegotiateRequest):
    stance_map = {
        "friendly": "mild improvements protecting lessee without being too strict",
        "firm": "balanced improvements protecting lessee fairly",
        "aggressive": "strong changes maximizing protection for the lessee"
    }

    if payload.option not in stance_map:
        raise HTTPException(status_code=400, detail="Invalid stance option")

    prompt = f"""
You are a contract negotiation assistant. 
The following clause is under review:

Original Clause (ID {payload.clause_id}):
\"\"\"{payload.original_clause}\"\"\"

Current risk level: {payload.current_risk}
Stance: {stance_map[payload.option]}

Instructions:
1. Explain how this clause impacts the lessee in simple terms.
2. Suggest 2–3 counter statements that make the clause safer or less risky 
   for the lessee while still being realistic.
3. Suggest a new risk level (red, yellow, green) after applying your counter statements.
4. Suggest 2–3 next actions (like Accept, Counter, Ask-human-lawyer).

Respond strictly in JSON with these keys:
{{
  "ai_explanation": "...",
  "counter_statements": ["...", "..."],
  "risk_after": "red|yellow|green",
  "next_actions": ["...", "..."]
}}
"""

    try:
        response = groq_client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
            max_tokens=500,
        )

        content = response.choices[0].message.content.strip()

        # Try to extract JSON using regex
        json_match = re.search(r"\{.*\}", content, re.DOTALL)
        if not json_match:
            raise ValueError("No valid JSON found in model response")

        parsed = json.loads(json_match.group())

        return NegotiateResponse(
            clause_id=payload.clause_id,
            option=payload.option,
            original_clause=payload.original_clause,
            ai_explanation=parsed.get("ai_explanation", "No explanation generated."),
            counter_statements=parsed.get("counter_statements", [
                "Counter-statement unavailable.",
                "Please consult a lawyer."
            ]),
            risk_after=parsed.get("risk_after", payload.current_risk),
            next_actions=parsed.get("next_actions", ["Accept", "Counter", "Ask-human-lawyer"])
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"AI negotiation failed: {str(e)}")

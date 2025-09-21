from fastapi import APIRouter, HTTPException
from app.config import groq_client
from app.models import NegotiateRequest, NegotiateResponse
import json
import re
import logging

router = APIRouter()

@router.post("/negotiate", response_model=NegotiateResponse)
async def negotiate_clause(payload: NegotiateRequest):
    # Map tone to negotiation stance
    tone_map = {
        "friendly": "mild improvements protecting lessee without being too strict",
        "firm": "balanced improvements protecting lessee fairly",
        "aggressive": "strong changes maximizing protection for the lessee"
    }

    # Validate the tone
    if payload.tone not in tone_map:
        raise HTTPException(status_code=400, detail="Invalid tone option")

    # Generate the prompt for the AI model
    prompt = f"""
You are a contract negotiation assistant. 
The following clause is under review:

Original Clause (ID {payload.clauseId}):
\"\"\"{payload.origin}\"\"\"

Stance: {tone_map[payload.tone]}
Current Risk Level: {payload.risk}

Instructions:
1. Rewrite the clause to make it less harmful for the lessee while maintaining realism.
2. Explain how the rewritten clause improves the lessee's position.
3. Suggest a new risk level (red, yellow, green) after applying the rewritten clause.

Respond strictly in JSON with these keys:
{{
  "rewritten_clause": "...",
  "ai_explanation": "...",
  "risk_after": "red|yellow|green"
}}
"""

    try:
        # Call the Groq LLM API
        response = groq_client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
            max_tokens=500,
        )

        content = response.choices[0].message.content.strip()

        # Extract JSON from the response
        json_match = re.search(r"\{.*\}", content, re.DOTALL)
        if not json_match:
            raise ValueError("No valid JSON found in model response")

        parsed = json.loads(json_match.group())
        logging.info(f"AI Response Parsed: {parsed}")
        # Return the response in the required format
        return NegotiateResponse(
            rewritten_clause=parsed.get("rewritten_clause", "No rewritten clause generated."),
            ai_explanation=parsed.get("ai_explanation", "No explanation generated."),
            risk_after=parsed.get("risk_after", "yellow"),  # Default to yellow if not provided
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"AI negotiation failed: {str(e)}")
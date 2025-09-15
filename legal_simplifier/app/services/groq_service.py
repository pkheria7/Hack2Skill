"""
Thin async wrapper around Groq chat-completion.
All generative features (eli5, rewrite, negotiate, chat, etc.) go through here.
"""
import os
from typing import List
from groq import AsyncGroq

client = AsyncGroq(api_key=os.getenv("GROQ_API_KEY"))

async def ask_groq(
    system: str,
    human: str,
    model: str = "llama3-70b-8192",
    temperature: float = 0.25,
    max_tokens: int = 1024,
) -> str:
    """
    Unified helper to hit Groq chat-completion.
    Returns the assistant string.
    """
    resp = await client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": human},
        ],
        temperature=temperature,
        max_tokens=max_tokens,
    )
    return resp.choices[0].message.content.strip()

# ---------- convenience builders below ----------

async def eli5_clause(clause_text: str, clause_type: str) -> str:
    system = "You are a legal explainer for non-lawyers. Reply in 1 short sentence."
    human = f"Explain this {clause_type} clause like I'm 5:\n\n{clause_text}"
    return await ask_groq(system, human)

async def rewrite_options(
    clause_text: str,
    clause_type: str,
    n: int = 3,
) -> List[str]:
    system = (
        "You are a legal editor. Produce exactly "
        f"{n} alternative wordings that are fairer or clearer. "
        "Number each line like 1. 2. 3."
    )
    human = f"Clause type: {clause_type}\n\nCurrent text:\n{clause_text}"
    raw = await ask_groq(system, human)
    # simple parser
    return [line.strip().split(" ", 1)[1] for line in raw.splitlines() if line.strip()]

async def negotiate_text(
    clause_text: str,
    stance: str,  # friendly | firm | aggressive
) -> str:
    system = (
        "You are a contract negotiator. "
        f"Tone: {stance}. "
        "Reply with a single concise counter-proposal."
    )
    human = f"Original clause:\n{clause_text}"
    return await ask_groq(system, human)
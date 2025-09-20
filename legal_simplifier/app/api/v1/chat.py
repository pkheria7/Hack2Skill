import os
import json
import uuid
from fastapi import APIRouter, HTTPException
from app.models import ChatRequest
from app.config import ask_groq

router = APIRouter(tags=["Chat Assistant"])

# Folder to store session files
SESSIONS_DIR = "sessions"
os.makedirs(SESSIONS_DIR, exist_ok=True)

# In-memory cache for quick access
conversation_history = {}

def load_doc_context(uid: str) -> str:
    """Load all clauses for a document UID into a single context string"""
    doc_dir = os.path.join("store", uid)
    if not os.path.exists(doc_dir):
        raise HTTPException(404, "document not found")

    context = ""
    files = sorted([f for f in os.listdir(doc_dir) if f.endswith(".txt")])
    for idx, f in enumerate(files, start=1):
        with open(os.path.join(doc_dir, f), "r", encoding="utf-8") as clause_file:
            context += f"Clause {idx}: {clause_file.read().strip()}\n"
    return context


# ---------------- Session Persistence ---------------- #
def save_session(session_id: str):
    """Save session history to a JSON file"""
    filepath = os.path.join(SESSIONS_DIR, f"{session_id}.json")
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(conversation_history[session_id], f, indent=2)


def load_session(session_id: str):
    """Load session history from file if exists"""
    filepath = os.path.join(SESSIONS_DIR, f"{session_id}.json")
    if os.path.exists(filepath):
        with open(filepath, "r", encoding="utf-8") as f:
            conversation_history[session_id] = json.load(f)


# ---------------- Chat Endpoint ---------------- #
@router.post("/chat")
async def chat(body: ChatRequest):
    context = load_doc_context(body.uid)

    # Use provided session_id or create new one
    session_id = body.session_id or str(uuid.uuid4())

    # Load from file if exists
    if session_id not in conversation_history:
        load_session(session_id)
    if session_id not in conversation_history:
        conversation_history[session_id] = []

    history = conversation_history[session_id]

    # Add user turn
    history.append({"role": "user", "content": body.question})

    # Keep last 6 turns in context
    conversation_str = ""
    for turn in history[-6:]:
        conversation_str += f"{turn['role'].capitalize()}: {turn['content']}\n"

    # Enhanced dual-mode prompt
    prompt = f"""
You are a specialized AI assistant trained to analyze and explain LEGAL CONTRACT CLAUSES.
You have access to the clauses of a contract and the ongoing conversation history.
Your role is to act like a precise, reliable, and user-friendly legal explainer.

## Core Behavior Guidelines:
1. **Grounding**:
   - Always base answers ONLY on the provided contract clauses and conversation history.
   - Never invent or assume terms not found in the clauses.
   - If the question is unrelated to the clauses, reply: "I am not sure, please check with a lawyer."

2. **Clause Citation**:
   - Always cite the exact clause number(s) you are referring to.
   - Example: "Clause 5 states …" or "Both Clause 2 and Clause 8 cover this issue."

3. **Dual Answering Modes**:
   - **Specific Question Mode** (user asks about a clause, phrase, or term):
     - Restate the relevant clause(s).
     - Explain their meaning in plain legal English.
     - Optionally, use a simple analogy or example.
   - **General Question Mode** (broad Qs like "Is there any issue?", "What should I watch out for?"):
     - Summarize the **top 2–3 most important clauses** that may create issues or obligations.
     - Keep it **short and focused**, not a clause-by-clause dump.
     - Highlight the risk in plain terms, then reference clause numbers.

4. **Formatting**:
   - Use bullet points or numbered lists if multiple clauses are relevant.
   - Highlight key legal terms in quotes.

5. **Follow-up Context**:
   - If the user asks about a term from a previous clause or your prior answer,
     explain it using the same clause context.
   - Re-use the last cited clause(s) unless the question explicitly shifts context.

6. **Tone**:
   - Neutral, professional, and concise.
   - Think like a junior lawyer explaining things simply to a client.

---

## Contract Clauses:
{context}

## Conversation so far:
{conversation_str}

## User’s Current Question:
{body.question}

Now, provide the best possible structured answer following the rules above.
"""

    try:
        answer = ask_groq(prompt)
        # Save bot turn
        history.append({"role": "assistant", "content": answer})
        # Persist to file
        save_session(session_id)
        return {"answer": answer, "session_id": session_id}
    except Exception as e:
        raise HTTPException(500, f"Chatbot error: {e}")


# ---------------- Session Management Endpoints ---------------- #
@router.get("/sessions")
async def list_sessions():
    """List all saved session IDs"""
    files = [f.replace(".json", "") for f in os.listdir(SESSIONS_DIR) if f.endswith(".json")]
    return {"sessions": files}


@router.get("/sessions/{session_id}")
async def get_session(session_id: str):
    """Retrieve full conversation history for a session"""
    filepath = os.path.join(SESSIONS_DIR, f"{session_id}.json")
    if not os.path.exists(filepath):
        raise HTTPException(404, "Session not found")
    with open(filepath, "r", encoding="utf-8") as f:
        data = json.load(f)
    return {"session_id": session_id, "history": data}

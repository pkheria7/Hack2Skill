"""
Chat assistant endpoint – streaming answer via Server-Sent Events
POST /api/v1/chat  (JSON body: {uid, question})
"""
import asyncio
import json
from typing import AsyncGenerator
from fastapi import APIRouter, Request, HTTPException
from sse_starlette.sse import EventSourceResponse
from app.services.groq_service import ask_groq

router = APIRouter()

WORD_DELAY_SEC = 0.04  # tweak to taste

async def _stream_answer(question: str) -> AsyncGenerator[str, None]:
    """
    1. Get full answer from Groq
    2. Yield each word with a tiny delay
    """
    system = (
        "You are a helpful legal assistant that answers questions "
        "about contracts in plain English. Keep answers short."
    )
    answer = await ask_groq(system, question)

    for word in answer.split():
        yield word + " "
        await asyncio.sleep(WORD_DELAY_SEC)

@router.post("/chat")
async def chat_endpoint(request: Request):
    """
    Accept JSON {uid: str, question: str}
    Return text/event-stream
    """
    try:
        body = await request.json()
        uid: str = body["uid"]
        question: str = body["question"]
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON body")

    async def event_generator() -> AsyncGenerator[dict, None]:
        async for word in _stream_answer(question):
            yield {"data": word}

    return EventSourceResponse(event_generator())
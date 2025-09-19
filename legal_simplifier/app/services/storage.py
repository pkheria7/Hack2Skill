# app/services/storage.py
import os
from fastapi import HTTPException

def load_clauses(uid: str):
    """Load document text from /store/<uid> and split into clauses"""
    doc_dir = os.path.join("store", uid)
    if not os.path.exists(doc_dir):
        raise HTTPException(404, "document not found")

    text_parts = []
    for f in os.listdir(doc_dir):
        if f.endswith(".txt"):
            with open(os.path.join(doc_dir, f), "r", encoding="utf-8") as infile:
                text_parts.append(infile.read())

    full_text = "\n".join(text_parts)

    clauses = [c.strip() for c in full_text.split("\n") if c.strip()]
    return clauses

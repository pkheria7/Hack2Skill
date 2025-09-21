# app/config.py
import os
from groq import Groq

# Initialize Groq client
groq_client = Groq(api_key=os.getenv("GROQ_API_KEY"))

def ask_groq(prompt: str) -> str:
    """Send a prompt to Groq and return raw text"""
    response = groq_client.chat.completions.create(
        model="llama-3.1-8b-instant",   # ✅ valid Groq model
        messages=[{"role": "user", "content": prompt}],
        temperature=0.2,
        max_tokens=512
    )
    return response.choices[0].message.content.strip()



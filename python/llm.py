from __future__ import annotations
import ollama
from config import CHAT_MODEL, OLLAMA_HOST

def generate_answer(system_prompt: str, user_prompt: str) -> str:
    response = ollama.Client(host=OLLAMA_HOST).chat(
        model=CHAT_MODEL,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        options={"temperature": 0.2, "top_p": 0.9},
    )
    return response["message"]["content"].strip()

from __future__ import annotations
from dataclasses import dataclass
from config import RAG_TOP_K
from llm import generate_answer
from prompt_builder import SYSTEM_PROMPT, build_user_prompt
from retriever import RetrievedDocument, retrieve

@dataclass(frozen=True)
class RagResult:
    question: str
    answer: str
    sources: list[RetrievedDocument]

def ask(
    question: str,
    top_k: int = RAG_TOP_K,
    document_type: str | None = None,
    city: str | None = None,
    status: str | None = None,
) -> RagResult:
    question = question.strip()
    if not question:
        raise ValueError("La question ne peut pas être vide.")
    sources = retrieve(question, top_k, document_type, city, status)
    prompt = build_user_prompt(question, sources)
    answer = generate_answer(SYSTEM_PROMPT, prompt)
    return RagResult(question, answer, sources)

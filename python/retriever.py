from __future__ import annotations
from dataclasses import dataclass
from typing import Any
import ollama
import psycopg
from pgvector import Vector
from pgvector.psycopg import register_vector
from psycopg.rows import dict_row
from config import EMBEDDING_MODEL, OLLAMA_HOST, RAG_MIN_SIMILARITY, RAG_TOP_K, pg_dsn

@dataclass(frozen=True)
class RetrievedDocument:
    document_id: int
    document_type: str
    building_id: int | None
    project_id: int | None
    title: str
    content: str
    metadata: dict[str, Any]
    similarity: float

    @property
    def citation(self) -> str:
        if self.document_type == "project" and self.project_id is not None:
            return f"[P:{self.project_id}]"
        if self.building_id is not None:
            return f"[B:{self.building_id}]"
        return f"[D:{self.document_id}]"

def embed_question(question: str) -> Vector:
    response = ollama.Client(host=OLLAMA_HOST).embed(
        model=EMBEDDING_MODEL,
        input=question,
    )
    return Vector(response["embeddings"][0])

def retrieve(
    question: str,
    top_k: int = RAG_TOP_K,
    document_type: str | None = None,
    city: str | None = None,
    status: str | None = None,
    min_similarity: float = RAG_MIN_SIMILARITY,
) -> list[RetrievedDocument]:
    query_vector = embed_question(question)
    filters = ["embedding IS NOT NULL"]
    params: list[Any] = [query_vector]

    if document_type:
        filters.append("document_type = %s")
        params.append(document_type)
    if city:
        filters.append("metadata ->> 'city' = %s")
        params.append(city)
    if status:
        filters.append("metadata ->> 'status' = %s")
        params.append(status)

    sql = f"""
        SELECT document_id, document_type, building_id, project_id,
               title, content, metadata,
               1 - (embedding <=> %s) AS similarity
        FROM building_documents
        WHERE {' AND '.join(filters)}
        ORDER BY embedding <=> %s
        LIMIT %s
    """
    params.extend([query_vector, top_k])

    with psycopg.connect(pg_dsn()) as conn:
        register_vector(conn)
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute(sql, params)
            rows = cur.fetchall()

    return [
        RetrievedDocument(
            document_id=row["document_id"],
            document_type=row["document_type"],
            building_id=row["building_id"],
            project_id=row["project_id"],
            title=row["title"],
            content=row["content"],
            metadata=row["metadata"],
            similarity=float(row["similarity"]),
        )
        for row in rows
        if float(row["similarity"]) >= min_similarity
    ]

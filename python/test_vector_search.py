from __future__ import annotations

import argparse

import ollama
import psycopg
from pgvector import Vector
from pgvector.psycopg import register_vector
from psycopg.rows import dict_row

from config import EMBEDDING_MODEL, OLLAMA_HOST, pg_dsn


def main() -> None:
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "question",
        nargs="?",
        default="Quels bâtiments anciens et mal isolés sont prioritaires ?",
    )

    parser.add_argument(
        "--limit",
        type=int,
        default=8,
    )

    args = parser.parse_args()

    client = ollama.Client(host=OLLAMA_HOST)

    query_embedding = client.embed(
        model=EMBEDDING_MODEL,
        input=args.question,
    )["embeddings"][0]

    query_vector = Vector(query_embedding)

    with psycopg.connect(pg_dsn()) as conn:
        register_vector(conn)

        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute("""
                SELECT
                    document_id,
                    document_type,
                    building_id,
                    project_id,
                    title,
                    1 - (embedding <=> %s) AS cosine_similarity,
                    LEFT(content, 350) AS excerpt
                FROM building_documents
                WHERE embedding IS NOT NULL
                ORDER BY embedding <=> %s
                LIMIT %s
            """, (
                query_vector,
                query_vector,
                args.limit,
            ))

            results = cur.fetchall()

    print(f"\nQuestion : {args.question}\n")

    for rank, row in enumerate(results, start=1):
        similarity = float(row["cosine_similarity"])

        print(
            f"{rank}. {row['title']} | "
            f"type={row['document_type']} | "
            f"similarité={similarity:.4f}"
        )

        print(f"   {row['excerpt']}...\n")


if __name__ == "__main__":
    main()
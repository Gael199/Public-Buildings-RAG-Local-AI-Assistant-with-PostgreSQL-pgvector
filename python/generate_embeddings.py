from __future__ import annotations

import time

import ollama
import psycopg
from pgvector.psycopg import register_vector
from psycopg.rows import dict_row

from config import (
    BATCH_SIZE,
    EMBEDDING_MODEL,
    EXPECTED_VECTOR_DIMENSION,
    OLLAMA_HOST,
    pg_dsn,
)


def batches(items: list[dict], size: int):
    for start in range(0, len(items), size):
        yield items[start:start + size]


def main() -> None:
    client = ollama.Client(host=OLLAMA_HOST)

    # Test rapide : le modèle doit exister et produire 768 dimensions.
    test = client.embed(
        model=EMBEDDING_MODEL,
        input="Test de dimension pour pgvector.",
    )
    dimension = len(test["embeddings"][0])

    print(f"Modèle d'embedding : {EMBEDDING_MODEL}")
    print(f"Dimension retournée : {dimension}")

    if dimension != EXPECTED_VECTOR_DIMENSION:
        raise RuntimeError(
            f"La table attend VECTOR({EXPECTED_VECTOR_DIMENSION}), "
            f"mais le modèle retourne {dimension} dimensions."
        )

    with psycopg.connect(pg_dsn()) as conn:
        register_vector(conn)

        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute("""
                SELECT document_id, content
                FROM building_documents
                WHERE embedding IS NULL
                ORDER BY document_id
            """)
            documents = cur.fetchall()

        if not documents:
            print("Tous les documents possèdent déjà un embedding.")
            return

        total = len(documents)
        completed = 0
        start_time = time.perf_counter()

        for group in batches(documents, BATCH_SIZE):
            response = client.embed(
                model=EMBEDDING_MODEL,
                input=[item["content"] for item in group],
            )
            vectors = response["embeddings"]

            if len(vectors) != len(group):
                raise RuntimeError("Ollama n'a pas retourné un vecteur par document.")

            with conn.cursor() as cur:
                cur.executemany(
                    """
                    UPDATE building_documents
                    SET embedding = %s
                    WHERE document_id = %s
                    """,
                    [
                        (vector, item["document_id"])
                        for item, vector in zip(group, vectors)
                    ],
                )
            conn.commit()

            completed += len(group)
            elapsed = time.perf_counter() - start_time
            print(
                f"Embeddings enregistrés : {completed}/{total} "
                f"({elapsed:.1f} secondes)"
            )

        with conn.cursor() as cur:
            cur.execute("""
                SELECT
                    COUNT(*) AS total,
                    COUNT(embedding) AS embedded,
                    MIN(vector_dims(embedding)) AS min_dimension,
                    MAX(vector_dims(embedding)) AS max_dimension
                FROM building_documents
            """)
            total_count, embedded_count, min_dim, max_dim = cur.fetchone()

    print(f"Documents totaux : {total_count}")
    print(f"Documents vectorisés : {embedded_count}")
    print(f"Dimensions : {min_dim} à {max_dim}")

    if total_count != embedded_count:
        raise RuntimeError("Certains documents n'ont pas reçu d'embedding.")

    print("Génération des embeddings réussie.")


if __name__ == "__main__":
    main()

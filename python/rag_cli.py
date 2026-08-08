from __future__ import annotations
import argparse
from rag_engine import ask

def main() -> None:
    parser = argparse.ArgumentParser(description="Assistant RAG local.")
    parser.add_argument("question")
    parser.add_argument("--top-k", type=int, default=8)
    parser.add_argument("--document-type", choices=["building", "project"])
    parser.add_argument("--city")
    parser.add_argument("--status")
    args = parser.parse_args()

    result = ask(
        args.question,
        args.top_k,
        args.document_type,
        args.city,
        args.status,
    )

    print("\nRÉPONSE\n")
    print(result.answer)
    print("\nSOURCES\n")
    for i, source in enumerate(result.sources, start=1):
        print(f"{i}. {source.citation} {source.title} | similarité={source.similarity:.4f}")

if __name__ == "__main__":
    main()

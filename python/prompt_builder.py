from __future__ import annotations
from retriever import RetrievedDocument

SYSTEM_PROMPT = """
Tu es l'assistant décisionnel d'une collectivité territoriale française.
Réponds uniquement à partir des sources fournies.
N'invente aucun bâtiment, projet, chiffre, coût, économie ou causalité.
Cite chaque constat avec [B:id] ou [P:id].
Si les sources ne suffisent pas, dis-le clairement.
Distingue les constats, l'interprétation et les recommandations.
Pour un calcul exhaustif, recommande SQL ou Power BI.
Réponds en français, clairement et professionnellement.
""".strip()

def build_user_prompt(question: str, documents: list[RetrievedDocument]) -> str:
    if not documents:
        return f"QUESTION\n{question}\n\nCONTEXTE\nAucune source pertinente retrouvée."
    context = "\n\n---\n\n".join(
        f"{doc.citation} {doc.title}\nSimilarité : {doc.similarity:.4f}\n{doc.content}"
        for doc in documents
    )
    return f"""
QUESTION
{question}

SOURCES RÉCUPÉRÉES
{context}

RÉPONSE ATTENDUE
Réponds directement, cite les sources et termine par une courte recommandation si elle est justifiée.
""".strip()

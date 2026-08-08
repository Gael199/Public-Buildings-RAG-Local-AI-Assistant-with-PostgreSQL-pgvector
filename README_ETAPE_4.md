# Étape 4 — Moteur RAG local avec Llama 3.1

## Copier les fichiers
Copier le contenu du dossier `python` dans le dossier `python` du projet existant.

## Installer les dépendances
```powershell
.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

## Vérifier Ollama
```powershell
ollama list
```

Les modèles `nomic-embed-text` et `llama3.1` doivent être présents.

## Tester le RAG
```powershell
python python\rag_cli.py "Quels projets d'isolation ont produit de bonnes économies ?"
```

Avec filtres :
```powershell
python python\rag_cli.py "Quels projets d'isolation ont produit de bonnes économies ?" --document-type project --status Completed
```

Par ville :
```powershell
python python\rag_cli.py "Quels bâtiments semblent énergivores ?" --document-type building --city Lyon
```

## Pipeline
Question → nomic-embed-text → pgvector → Top K documents → contexte → Llama 3.1 → réponse sourcée.

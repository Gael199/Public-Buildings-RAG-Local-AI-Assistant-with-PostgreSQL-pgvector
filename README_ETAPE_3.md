# Étape 3 — Documents RAG et embeddings locaux avec Ollama

## Résultat de cette étape

La table `building_documents` contiendra :

- 500 documents décrivant les bâtiments ;
- 900 documents décrivant les projets ;
- 1 400 embeddings de 768 dimensions.

## 1. Copier les fichiers

Copier dans le projet existant :

```text
python/config.py
python/generate_documents.py
python/generate_embeddings.py
python/test_vector_search.py
sql/verification_etape_3.sql
```

Remplacer également `requirements.txt` et compléter `.env`.

## 2. Installer les modèles Ollama

Dans PowerShell :

```powershell
ollama pull nomic-embed-text
ollama pull llama3.1
ollama list
```

`nomic-embed-text` produit les embeddings.  
`llama3.1` sera utilisé à l'étape suivante pour rédiger les réponses.

## 3. Installer les dépendances Python

```powershell
.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

## 4. Générer les documents textuels

```powershell
python python\generate_documents.py
```

Résultat attendu :

```text
Documents créés : 1400
Documents bâtiments : 500
Documents projets : 900
Embeddings déjà présents : 0
Création des documents réussie.
```

## 5. Générer les embeddings

Vérifier qu'Ollama est lancé, puis :

```powershell
python python\generate_embeddings.py
```

Le traitement local peut prendre plusieurs minutes.

Résultat final attendu :

```text
Documents totaux : 1400
Documents vectorisés : 1400
Dimensions : 768 à 768
Génération des embeddings réussie.
```

## 6. Tester pgvector

```powershell
python python\test_vector_search.py
```

Ou avec une question personnalisée :

```powershell
python python\test_vector_search.py "Quels projets d'isolation ont produit de bonnes économies ?"
```

## 7. Vérification dans pgAdmin

Ouvrir et exécuter :

```text
sql/verification_etape_3.sql
```

## Important

Le même modèle d'embedding doit être utilisé pour :

- vectoriser les documents ;
- vectoriser les questions.

La table actuelle utilise `VECTOR(768)`, compatible avec
`nomic-embed-text`.

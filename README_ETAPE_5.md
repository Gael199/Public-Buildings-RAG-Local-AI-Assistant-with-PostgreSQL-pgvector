# Étape 5 — Interface Streamlit

## 1. Copier les fichiers

Copier :

```text
streamlit/app.py
sql/05_views_powerbi.sql
```

dans le projet existant.

Remplacer également `requirements.txt`.

## 2. Installer les dépendances

```powershell
.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

## 3. Vérifier les services

Docker doit fonctionner :

```powershell
docker ps
```

Ollama doit fonctionner :

```powershell
ollama list
```

## 4. Lancer Streamlit

À la racine du projet :

```powershell
streamlit run streamlit\app.py
```

Le navigateur doit ouvrir :

```text
http://localhost:8501
```

## 5. Fonctionnalités

L'application contient :

- Assistant IA avec Llama 3.1 ;
- recherche sémantique pgvector ;
- filtres par type, ville et statut ;
- affichage des sources et scores ;
- tableau de bord métier.

## 6. Préparer Power BI

Dans pgAdmin, exécuter :

```text
sql/05_views_powerbi.sql
```

Les vues créées seront :

```text
vw_powerbi_buildings
vw_powerbi_projects
```

Power BI sera traité à l'étape suivante.

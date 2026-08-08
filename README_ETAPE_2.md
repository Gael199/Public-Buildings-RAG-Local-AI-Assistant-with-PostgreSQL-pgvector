# Étape 2 — Chargement des CSV dans PostgreSQL

## 1. Copier le fichier de configuration

Dans PowerShell, à la racine du projet :

```powershell
Copy-Item .env.example .env
```

## 2. Créer et activer l'environnement Python

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```

## 3. Installer les dépendances

```powershell
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

## 4. Exécuter le chargement

```powershell
python python\load_data.py
```

Résultat attendu :

```text
Import terminé : 500 bâtiments et 900 projets.
Bâtiments chargés : 500
Projets chargés : 900
Bâtiments sans projet : environ 75
```

## 5. Vérifier dans pgAdmin

```sql
SELECT COUNT(*) FROM buildings;
SELECT COUNT(*) FROM renovation_projects;

SELECT COUNT(*) AS buildings_without_project
FROM buildings b
LEFT JOIN renovation_projects p
    ON p.building_id = b.building_id
WHERE p.project_id IS NULL;
```

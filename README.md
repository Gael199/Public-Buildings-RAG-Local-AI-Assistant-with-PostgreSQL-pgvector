# Données corrigées — Étape 2B

Cette version garantit :
- 500 bâtiments ;
- 900 projets ;
- exactement 75 bâtiments sans projet ;
- au moins un projet pour chacun des 425 autres bâtiments ;
- des projets récurrents ;
- une saisonnalité printemps/été ;
- des montants d'aides inférieurs au coût de référence ;
- des économies énergétiques corrélées aux travaux.

## Remplacement

Copier le contenu de ce dossier dans le projet existant en remplaçant :
- `data/buildings.csv`
- `data/renovation_projects.csv`
- `python/load_data.py`

## Exécution

```powershell
.venv\Scripts\Activate.ps1
python python\load_data.py
```

Résultat attendu :

```text
Bâtiments chargés : 500
Projets chargés : 900
Bâtiments sans projet : 75
Contrôles qualité réussis.
```

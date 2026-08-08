from __future__ import annotations

import csv
import os
from pathlib import Path
from typing import Any

import psycopg
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"
load_dotenv(ROOT / ".env")

def dsn() -> str:
    return (
        f"host={os.getenv('PGHOST', 'localhost')} "
        f"port={os.getenv('PGPORT', '5433')} "
        f"dbname={os.getenv('PGDATABASE', 'public_buildings_rag')} "
        f"user={os.getenv('PGUSER', 'postgres')} "
        f"password={os.getenv('PGPASSWORD', '')}"
    )

def nullable(value: str) -> Any:
    return None if value == "" else value

def parse_bool(value: str) -> bool | None:
    if value == "":
        return None
    return value.strip().lower() in {"true", "1", "yes", "oui"}

def read_csv(name: str) -> tuple[list[str], list[dict[str, Any]]]:
    path = DATA_DIR / name
    with path.open("r", encoding="utf-8-sig", newline="") as file:
        reader = csv.DictReader(file)
        return list(reader.fieldnames or []), list(reader)

def prepare_buildings(rows):
    nullable_fields = {
        "annual_energy_consumption_kwh", "energy_intensity_kwh_m2_year",
        "dpe_rating", "co2_emissions_kg_year", "last_energy_audit_year",
        "asbestos_risk",
    }
    for row in rows:
        for field in nullable_fields:
            row[field] = nullable(row[field])
        row["has_solar_panels"] = parse_bool(row["has_solar_panels"])
        row["asbestos_risk"] = parse_bool(row["asbestos_risk"]) if row["asbestos_risk"] is not None else None
    return rows

def prepare_projects(rows):
    nullable_fields = {
        "end_date", "actual_cost_eur", "cost_variance_percent",
        "actual_energy_savings_percent", "annual_energy_savings_kwh",
    }
    for row in rows:
        for field in nullable_fields:
            row[field] = nullable(row[field])
    return rows

def copy_rows(conn, table, columns, rows):
    with conn.cursor() as cur:
        with cur.copy(f"COPY {table} ({', '.join(columns)}) FROM STDIN") as copy:
            for row in rows:
                copy.write_row([row[column] for column in columns])

def main():
    building_columns, buildings = read_csv("buildings.csv")
    project_columns, projects = read_csv("renovation_projects.csv")
    buildings = prepare_buildings(buildings)
    projects = prepare_projects(projects)

    try:
        with psycopg.connect(dsn()) as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "TRUNCATE TABLE building_documents, renovation_projects, buildings "
                    "RESTART IDENTITY CASCADE"
                )
            copy_rows(conn, "buildings", building_columns, buildings)
            copy_rows(conn, "renovation_projects", project_columns, projects)
            conn.commit()

            with conn.cursor() as cur:
                cur.execute("SELECT COUNT(*) FROM buildings")
                bcount = cur.fetchone()[0]
                cur.execute("SELECT COUNT(*) FROM renovation_projects")
                pcount = cur.fetchone()[0]
                cur.execute("""
                    SELECT COUNT(*)
                    FROM buildings b
                    LEFT JOIN renovation_projects p USING (building_id)
                    WHERE p.project_id IS NULL
                """)
                no_project = cur.fetchone()[0]

            print(f"Bâtiments chargés : {bcount}")
            print(f"Projets chargés : {pcount}")
            print(f"Bâtiments sans projet : {no_project}")

            if (bcount, pcount, no_project) != (500, 900, 75):
                raise RuntimeError(
                    "Contrôle qualité échoué : résultats attendus = 500, 900 et 75."
                )

            print("Contrôles qualité réussis.")

    except psycopg.Error as exc:
        raise SystemExit(f"Erreur PostgreSQL : {exc}") from exc

if __name__ == "__main__":
    main()

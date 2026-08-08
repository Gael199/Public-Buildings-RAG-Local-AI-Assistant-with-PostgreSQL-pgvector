from __future__ import annotations

import json

import psycopg
from psycopg.rows import dict_row

from config import pg_dsn


def display(value, suffix: str = "") -> str:
    if value is None:
        return "non renseigné"
    return f"{value}{suffix}"


def building_document(row: dict) -> tuple:
    title = f"Bâtiment {row['building_id']} — {row['building_name']}"

    content = f"""
Fiche du bâtiment public {row['building_name']}.
Identifiant bâtiment : {row['building_id']}.
Type : {row['building_type']}.
Localisation : {row['address']}, {row['postal_code']} {row['city']}.
Année de construction : {row['construction_year']}.
Surface : {row['surface_m2']} m² sur {row['number_of_floors']} étage(s).
Chauffage : {row['heating_type']}.
DPE : {display(row['dpe_rating'])}.
Qualité d'isolation : {row['insulation_quality']}.
Consommation annuelle : {display(row['annual_energy_consumption_kwh'], ' kWh')}.
Intensité énergétique : {display(row['energy_intensity_kwh_m2_year'], ' kWh/m²/an')}.
Émissions de CO2 : {display(row['co2_emissions_kg_year'], ' kg/an')}.
Taux d'occupation : {float(row['occupancy_rate']) * 100:.1f} %.
Nombre d'occupants : {row['number_of_occupants']}.
Panneaux solaires : {'oui' if row['has_solar_panels'] else 'non'}.
Dernier audit énergétique : {display(row['last_energy_audit_year'])}.
Accessibilité : {row['accessibility_status']}.
Risque amiante : {display(row['asbestos_risk'])}.
Statut patrimonial : {row['heritage_status']}.
Nombre de projets de rénovation : {row['project_count']}.
Coût estimé cumulé des projets : {row['total_estimated_cost_eur']} euros.
Coût réel cumulé connu : {row['total_actual_cost_eur']} euros.
Aides cumulées : {row['total_subsidy_eur']} euros.
Économies annuelles cumulées connues : {row['total_annual_energy_savings_kwh']} kWh.
""".strip()

    metadata = {
        "source_type": "building",
        "building_id": row["building_id"],
        "city": row["city"],
        "building_type": row["building_type"],
        "dpe_rating": row["dpe_rating"],
        "insulation_quality": row["insulation_quality"],
        "construction_year": row["construction_year"],
        "project_count": row["project_count"],
    }

    return (
        row["building_id"],
        None,
        "building",
        title,
        content,
        json.dumps(metadata, ensure_ascii=False),
    )


def project_document(row: dict) -> tuple:
    title = f"Projet {row['project_id']} — {row['project_type']}"

    content = f"""
Projet de rénovation {row['project_id']} concernant le bâtiment
{row['building_name']} (bâtiment {row['building_id']}).
Type de bâtiment : {row['building_type']}. Ville : {row['city']}.
Type de travaux : {row['project_type']}.
Statut du projet : {row['status']}.
Niveau de priorité : {row['priority_level']}.
Début : {row['start_date']}.
Fin planifiée : {row['planned_end_date']}.
Fin réelle : {display(row['end_date'])}.
Coût estimé : {row['estimated_cost_eur']} euros.
Coût réel connu : {display(row['actual_cost_eur'], ' euros')}.
Écart budgétaire : {display(row['cost_variance_percent'], ' %')}.
Montant des aides : {row['subsidy_amount_eur']} euros.
Source de financement : {row['funding_source']}.
Entreprise : {row['contractor_name']}.
Chef de projet : {row['project_manager']}.
Procédure de marché : {row['procurement_method']}.
Perturbation des activités : {row['works_disruption_level']}.
Économie d'énergie estimée : {row['estimated_energy_savings_percent']} %.
Économie d'énergie réelle : {display(row['actual_energy_savings_percent'], ' %')}.
Économie annuelle réelle : {display(row['annual_energy_savings_kwh'], ' kWh')}.
Contexte énergétique du bâtiment : DPE {display(row['dpe_rating'])},
isolation {row['insulation_quality']}, chauffage {row['heating_type']}.
""".strip()

    metadata = {
        "source_type": "project",
        "project_id": row["project_id"],
        "building_id": row["building_id"],
        "city": row["city"],
        "building_type": row["building_type"],
        "project_type": row["project_type"],
        "status": row["status"],
        "funding_source": row["funding_source"],
        "priority_level": row["priority_level"],
    }

    return (
        row["building_id"],
        row["project_id"],
        "project",
        title,
        content,
        json.dumps(metadata, ensure_ascii=False),
    )


def main() -> None:
    with psycopg.connect(pg_dsn()) as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute("""
                SELECT
                    b.*,
                    COUNT(p.project_id) AS project_count,
                    COALESCE(SUM(p.estimated_cost_eur), 0) AS total_estimated_cost_eur,
                    COALESCE(SUM(p.actual_cost_eur), 0) AS total_actual_cost_eur,
                    COALESCE(SUM(p.subsidy_amount_eur), 0) AS total_subsidy_eur,
                    COALESCE(SUM(p.annual_energy_savings_kwh), 0)
                        AS total_annual_energy_savings_kwh
                FROM buildings b
                LEFT JOIN renovation_projects p USING (building_id)
                GROUP BY b.building_id
                ORDER BY b.building_id
            """)
            buildings = cur.fetchall()

            cur.execute("""
                SELECT
                    p.*,
                    b.building_name,
                    b.building_type,
                    b.city,
                    b.dpe_rating,
                    b.insulation_quality,
                    b.heating_type
                FROM renovation_projects p
                JOIN buildings b USING (building_id)
                ORDER BY p.project_id
            """)
            projects = cur.fetchall()

        rows = [building_document(row) for row in buildings]
        rows += [project_document(row) for row in projects]

        with conn.cursor() as cur:
            cur.execute("TRUNCATE TABLE building_documents RESTART IDENTITY")

            with cur.copy("""
                COPY building_documents (
                    building_id,
                    project_id,
                    document_type,
                    title,
                    content,
                    metadata
                )
                FROM STDIN
            """) as copy:
                for row in rows:
                    copy.write_row(row)

        conn.commit()

        with conn.cursor() as cur:
            cur.execute("""
                SELECT
                    COUNT(*) AS total,
                    COUNT(*) FILTER (WHERE document_type = 'building') AS buildings,
                    COUNT(*) FILTER (WHERE document_type = 'project') AS projects,
                    COUNT(*) FILTER (WHERE embedding IS NOT NULL) AS embedded
                FROM building_documents
            """)
            total, building_count, project_count, embedded = cur.fetchone()

    print(f"Documents créés : {total}")
    print(f"Documents bâtiments : {building_count}")
    print(f"Documents projets : {project_count}")
    print(f"Embeddings déjà présents : {embedded}")

    if (total, building_count, project_count) != (1400, 500, 900):
        raise RuntimeError("Le nombre de documents créé ne correspond pas au résultat attendu.")

    print("Création des documents réussie.")


if __name__ == "__main__":
    main()

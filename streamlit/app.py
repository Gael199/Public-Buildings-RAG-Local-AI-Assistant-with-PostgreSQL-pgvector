from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd
import plotly.express as px
import psycopg
import streamlit as st
from psycopg.rows import dict_row

ROOT = Path(__file__).resolve().parents[1]
PYTHON_DIR = ROOT / "python"
sys.path.insert(0, str(PYTHON_DIR))

from config import pg_dsn
from rag_engine import ask


st.set_page_config(
    page_title="Assistant RAG — Bâtiments publics",
    page_icon="🏛️",
    layout="wide",
)


@st.cache_data(ttl=300)
def load_cities() -> list[str]:
    with psycopg.connect(pg_dsn()) as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT DISTINCT city
                FROM buildings
                ORDER BY city
            """)
            return [row[0] for row in cur.fetchall()]


@st.cache_data(ttl=300)
def load_dashboard_data() -> tuple[pd.DataFrame, pd.DataFrame]:
    with psycopg.connect(pg_dsn()) as conn:
        buildings = pd.read_sql_query(
            """
            SELECT
                building_id,
                building_name,
                building_type,
                city,
                construction_year,
                surface_m2,
                heating_type,
                dpe_rating,
                insulation_quality,
                annual_energy_consumption_kwh,
                energy_intensity_kwh_m2_year,
                co2_emissions_kg_year,
                latitude,
                longitude
            FROM buildings
            """,
            conn,
        )

        projects = pd.read_sql_query(
            """
            SELECT
                p.project_id,
                p.building_id,
                b.building_name,
                b.building_type,
                b.city,
                p.project_type,
                p.start_date,
                p.status,
                p.estimated_cost_eur,
                p.actual_cost_eur,
                p.subsidy_amount_eur,
                p.actual_energy_savings_percent
            FROM renovation_projects p
            JOIN buildings b USING (building_id)
            """,
            conn,
        )

    return buildings, projects


def source_card(source) -> None:
    st.markdown(
        f"""
**{source.citation} {source.title}**

- Type : `{source.document_type}`
- Similarité : `{source.similarity:.4f}`
- Ville : `{source.metadata.get("city", "non renseignée")}`
"""
    )
    st.write(source.content[:900] + ("..." if len(source.content) > 900 else ""))


st.title("🏛️ Assistant RAG — Bâtiments publics")
st.caption("PostgreSQL + pgvector + Ollama + Llama 3.1 + Streamlit")

tab_chat, tab_search, tab_dashboard = st.tabs([
    "Assistant IA",
    "Recherche sémantique",
    "Tableau de bord",
])

with st.sidebar:
    st.header("Paramètres")

    top_k = st.slider(
        "Nombre de sources",
        min_value=3,
        max_value=15,
        value=8,
    )

    source_label = st.selectbox(
        "Type de document",
        ["Tous", "Bâtiments", "Projets"],
    )

    document_type = {
        "Tous": None,
        "Bâtiments": "building",
        "Projets": "project",
    }[source_label]

    city_options = ["Toutes"] + load_cities()
    city_label = st.selectbox("Ville", city_options)
    city = None if city_label == "Toutes" else city_label

    status_options = ["Tous", "Completed", "In Progress", "Planned", "Cancelled"]
    status_label = st.selectbox("Statut du projet", status_options)
    status = None if status_label == "Tous" else status_label

    if document_type != "project":
        status = None

    st.divider()
    st.markdown("""
**Exemples de questions**

- Quels bâtiments anciens et mal isolés semblent prioritaires ?
- Quels projets d'isolation terminés ont produit de bonnes économies ?
- Quels bâtiments de Lyon semblent énergivores ?
- Résume les projets associés à un bâtiment donné.
""")


with tab_chat:
    st.subheader("Assistant conversationnel")

    if "messages" not in st.session_state:
        st.session_state.messages = []

    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    question = st.chat_input("Posez une question sur le patrimoine public…")

    if question:
        st.session_state.messages.append({
            "role": "user",
            "content": question,
        })

        with st.chat_message("user"):
            st.markdown(question)

        with st.chat_message("assistant"):
            try:
                with st.spinner("Recherche pgvector et génération avec Llama 3.1…"):
                    result = ask(
                        question=question,
                        top_k=top_k,
                        document_type=document_type,
                        city=city,
                        status=status,
                    )

                st.markdown(result.answer)

                with st.expander(
                    f"Sources utilisées ({len(result.sources)})",
                    expanded=False,
                ):
                    if not result.sources:
                        st.info("Aucune source pertinente n'a été retrouvée.")
                    else:
                        for source in result.sources:
                            source_card(source)
                            st.divider()

                st.session_state.messages.append({
                    "role": "assistant",
                    "content": result.answer,
                })

            except Exception as exc:
                st.error(f"Erreur : {exc}")


with tab_search:
    st.subheader("Recherche sémantique directe")

    search_question = st.text_input(
        "Texte à rechercher",
        value="projets d'isolation ayant produit de bonnes économies",
        key="search_question",
    )

    if st.button("Rechercher", type="primary"):
        try:
            from retriever import retrieve

            with st.spinner("Recherche vectorielle…"):
                results = retrieve(
                    question=search_question,
                    top_k=top_k,
                    document_type=document_type,
                    city=city,
                    status=status,
                )

            if not results:
                st.warning("Aucun résultat au-dessus du seuil de similarité.")
            else:
                dataframe = pd.DataFrame([
                    {
                        "citation": item.citation,
                        "titre": item.title,
                        "type": item.document_type,
                        "ville": item.metadata.get("city"),
                        "statut": item.metadata.get("status"),
                        "similarité": round(item.similarity, 4),
                        "extrait": item.content[:280],
                    }
                    for item in results
                ])

                st.dataframe(
                    dataframe,
                    use_container_width=True,
                    hide_index=True,
                )

                for item in results:
                    with st.expander(
                        f"{item.citation} {item.title} — {item.similarity:.4f}"
                    ):
                        st.write(item.content)

        except Exception as exc:
            st.error(f"Erreur : {exc}")


with tab_dashboard:
    st.subheader("Indicateurs métier")

    buildings, projects = load_dashboard_data()

    col1, col2, col3, col4 = st.columns(4)

    col1.metric("Bâtiments", f"{len(buildings):,}".replace(",", " "))
    col2.metric("Projets", f"{len(projects):,}".replace(",", " "))

    actual_cost = projects["actual_cost_eur"].fillna(0).sum()
    col3.metric("Coût réel connu", f"{actual_cost:,.0f} €".replace(",", " "))

    avg_savings = projects["actual_energy_savings_percent"].dropna().mean()
    col4.metric(
        "Économie réelle moyenne",
        "N/D" if pd.isna(avg_savings) else f"{avg_savings:.1f} %",
    )

    left, right = st.columns(2)

    with left:
        chart_data = (
            projects.groupby("project_type", as_index=False)["actual_cost_eur"]
            .sum()
            .sort_values("actual_cost_eur", ascending=True)
        )

        fig = px.bar(
            chart_data,
            x="actual_cost_eur",
            y="project_type",
            orientation="h",
            title="Coût réel par type de projet",
            labels={
                "actual_cost_eur": "Coût réel (€)",
                "project_type": "Type de projet",
            },
        )
        st.plotly_chart(fig, use_container_width=True)

    with right:
        energy_data = (
            buildings.groupby("building_type", as_index=False)[
                "energy_intensity_kwh_m2_year"
            ]
            .mean()
            .sort_values("energy_intensity_kwh_m2_year", ascending=False)
        )

        fig = px.bar(
            energy_data,
            x="building_type",
            y="energy_intensity_kwh_m2_year",
            title="Intensité énergétique moyenne par type",
            labels={
                "energy_intensity_kwh_m2_year": "kWh/m²/an",
                "building_type": "Type de bâtiment",
            },
        )
        st.plotly_chart(fig, use_container_width=True)

    status_data = (
        projects.groupby("status", as_index=False)["project_id"]
        .count()
        .rename(columns={"project_id": "project_count"})
    )

    fig = px.pie(
        status_data,
        names="status",
        values="project_count",
        title="Répartition des projets par statut",
    )
    st.plotly_chart(fig, use_container_width=True)

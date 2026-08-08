CREATE EXTENSION IF NOT EXISTS vector;

DROP TABLE IF EXISTS building_documents CASCADE;
DROP TABLE IF EXISTS renovation_projects CASCADE;
DROP TABLE IF EXISTS buildings CASCADE;

CREATE TABLE buildings (
    building_id INTEGER PRIMARY KEY,
    building_name VARCHAR(150) NOT NULL,
    building_type VARCHAR(60) NOT NULL,
    address VARCHAR(180) NOT NULL,
    city VARCHAR(100) NOT NULL,
    postal_code VARCHAR(10) NOT NULL,

    construction_year SMALLINT NOT NULL
        CHECK (construction_year BETWEEN 1900 AND 2020),

    surface_m2 NUMERIC(12,2) NOT NULL
        CHECK (surface_m2 > 0),

    number_of_floors SMALLINT NOT NULL
        CHECK (number_of_floors > 0),

    heating_type VARCHAR(60) NOT NULL,

    annual_energy_consumption_kwh NUMERIC(16,2),

    energy_intensity_kwh_m2_year NUMERIC(12,2),

    dpe_rating CHAR(1)
        CHECK (
            dpe_rating IS NULL
            OR dpe_rating IN ('A','B','C','D','E','F','G')
        ),

    co2_emissions_kg_year NUMERIC(16,2),

    insulation_quality VARCHAR(30),

    occupancy_rate NUMERIC(6,4)
        CHECK (
            occupancy_rate IS NULL
            OR occupancy_rate BETWEEN 0 AND 1
        ),

    number_of_occupants INTEGER
        CHECK (
            number_of_occupants IS NULL
            OR number_of_occupants >= 0
        ),

    has_solar_panels BOOLEAN NOT NULL DEFAULT FALSE,

    last_energy_audit_year SMALLINT,

    accessibility_status VARCHAR(50),

    asbestos_risk BOOLEAN,

    heritage_status VARCHAR(50),

    latitude NUMERIC(9,6),

    longitude NUMERIC(9,6)
);

CREATE TABLE renovation_projects (
    project_id INTEGER PRIMARY KEY,

    building_id INTEGER NOT NULL
        REFERENCES buildings(building_id)
        ON UPDATE CASCADE
        ON DELETE RESTRICT,

    project_type VARCHAR(100) NOT NULL,

    start_date DATE NOT NULL,

    planned_end_date DATE NOT NULL,

    end_date DATE,

    status VARCHAR(30) NOT NULL,

    estimated_cost_eur NUMERIC(16,2) NOT NULL
        CHECK (estimated_cost_eur >= 0),

    actual_cost_eur NUMERIC(16,2)
        CHECK (
            actual_cost_eur IS NULL
            OR actual_cost_eur >= 0
        ),

    cost_variance_percent NUMERIC(10,2),

    subsidy_amount_eur NUMERIC(16,2) NOT NULL
        CHECK (subsidy_amount_eur >= 0),

    funding_source VARCHAR(80),

    contractor_name VARCHAR(120),

    estimated_energy_savings_percent NUMERIC(7,2),

    actual_energy_savings_percent NUMERIC(7,2),

    annual_energy_savings_kwh NUMERIC(16,2),

    project_manager VARCHAR(100),

    procurement_method VARCHAR(100),

    priority_level VARCHAR(20),

    works_disruption_level VARCHAR(20),

    CHECK (planned_end_date >= start_date),

    CHECK (
        end_date IS NULL
        OR end_date >= start_date
    ),

    CHECK (
        subsidy_amount_eur <=
        COALESCE(actual_cost_eur, estimated_cost_eur)
    )
);

CREATE TABLE building_documents (
    document_id BIGSERIAL PRIMARY KEY,

    building_id INTEGER
        REFERENCES buildings(building_id)
        ON DELETE CASCADE,

    project_id INTEGER
        REFERENCES renovation_projects(project_id)
        ON DELETE CASCADE,

    document_type VARCHAR(30) NOT NULL
        CHECK (
            document_type IN (
                'building',
                'project',
                'audit',
                'summary'
            )
        ),

    title TEXT NOT NULL,

    content TEXT NOT NULL,

    metadata JSONB NOT NULL DEFAULT '{}'::jsonb,

    embedding VECTOR(768),

    created_at TIMESTAMPTZ NOT NULL
        DEFAULT CURRENT_TIMESTAMP,

    CHECK (
        building_id IS NOT NULL
        OR project_id IS NOT NULL
    )
);

CREATE INDEX idx_buildings_city
ON buildings(city);

CREATE INDEX idx_buildings_type
ON buildings(building_type);

CREATE INDEX idx_buildings_dpe
ON buildings(dpe_rating);

CREATE INDEX idx_projects_building_id
ON renovation_projects(building_id);

CREATE INDEX idx_projects_status
ON renovation_projects(status);

CREATE INDEX idx_projects_type
ON renovation_projects(project_type);

CREATE INDEX idx_documents_building_id
ON building_documents(building_id);

CREATE INDEX idx_documents_project_id
ON building_documents(project_id);

CREATE INDEX idx_documents_metadata
ON building_documents
USING GIN(metadata);

CREATE INDEX idx_documents_embedding_hnsw
ON building_documents
USING hnsw (embedding vector_cosine_ops)
WITH (
    m = 16,
    ef_construction = 64
);
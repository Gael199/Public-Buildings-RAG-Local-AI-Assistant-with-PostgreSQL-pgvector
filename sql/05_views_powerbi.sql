CREATE OR REPLACE VIEW vw_powerbi_buildings AS
SELECT
    b.building_id,
    b.building_name,
    b.building_type,
    b.address,
    b.city,
    b.postal_code,
    b.construction_year,
    b.surface_m2,
    b.number_of_floors,
    b.heating_type,
    b.annual_energy_consumption_kwh,
    b.energy_intensity_kwh_m2_year,
    b.dpe_rating,
    b.co2_emissions_kg_year,
    b.insulation_quality,
    b.occupancy_rate,
    b.number_of_occupants,
    b.has_solar_panels,
    b.latitude,
    b.longitude,
    COUNT(p.project_id) AS project_count,
    COALESCE(SUM(p.estimated_cost_eur), 0) AS total_estimated_cost_eur,
    COALESCE(SUM(p.actual_cost_eur), 0) AS total_actual_cost_eur,
    COALESCE(SUM(p.subsidy_amount_eur), 0) AS total_subsidy_eur,
    COALESCE(SUM(p.annual_energy_savings_kwh), 0)
        AS total_annual_energy_savings_kwh
FROM buildings b
LEFT JOIN renovation_projects p USING (building_id)
GROUP BY b.building_id;


CREATE OR REPLACE VIEW vw_powerbi_projects AS
SELECT
    p.project_id,
    p.building_id,
    b.building_name,
    b.building_type,
    b.city,
    b.postal_code,
    b.construction_year,
    b.surface_m2,
    b.dpe_rating,
    b.insulation_quality,
    b.latitude,
    b.longitude,
    p.project_type,
    p.start_date,
    p.planned_end_date,
    p.end_date,
    EXTRACT(YEAR FROM p.start_date)::integer AS project_year,
    EXTRACT(MONTH FROM p.start_date)::integer AS project_month,
    TO_CHAR(p.start_date, 'YYYY-MM') AS project_year_month,
    p.status,
    p.estimated_cost_eur,
    p.actual_cost_eur,
    p.cost_variance_percent,
    p.subsidy_amount_eur,
    p.funding_source,
    p.contractor_name,
    p.estimated_energy_savings_percent,
    p.actual_energy_savings_percent,
    p.annual_energy_savings_kwh,
    p.project_manager,
    p.procurement_method,
    p.priority_level,
    p.works_disruption_level,
    CASE
        WHEN p.actual_cost_eur IS NULL THEN NULL
        ELSE p.actual_cost_eur - p.subsidy_amount_eur
    END AS net_cost_after_subsidy_eur,
    CASE
        WHEN p.end_date IS NULL THEN NULL
        ELSE p.end_date - p.planned_end_date
    END AS schedule_variance_days
FROM renovation_projects p
JOIN buildings b USING (building_id);

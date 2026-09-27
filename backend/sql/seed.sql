-- Fictional demo data, not a copy of any local/customer database.
-- Fresh setup only; run after setup.sql, before Alembic. No account credentials.
BEGIN;
INSERT INTO customers (customer_id, name, date_of_birth, sex, education_level,
 occupation, hobbies, relationship, zip_code) VALUES
 ('C1001', 'Demo Customer One', '1990-01-01', 'MALE', 'College', 'tech-support', 'reading', 'unmarried', '00000'),
 ('C1002', 'Demo Customer Two', '1988-06-01', 'FEMALE', 'College', 'sales', 'reading', 'unmarried', '00000');
INSERT INTO policies (policy_id, customer_id, policy_number, policy_bind_date,
 policy_state, policy_csl, deductible, annual_premium, umbrella_limit,
 policy_end_date, policy_status, product_code, coverage_limit) VALUES
 ('P1001', 'C1001', 'DEMO-1001', '2025-01-01', 'OH', '250/500', 1000, 1200, 0,
  '2030-12-31', 'active', 'MOTOR_COMPREHENSIVE', 500000),
 ('P1002', 'C1002', 'DEMO-1002', '2025-01-01', 'OH', '100/300', 1000, 1000, 0,
  '2030-12-31', 'active', 'MOTOR_STANDARD', 300000);
INSERT INTO vehicles (customer_id, policy_id, make, model, year) VALUES
 ('C1001', 'P1001', 'Toyota', 'Corolla', 2020),
 ('C1002', 'P1002', 'Honda', 'Civic', 2021);
INSERT INTO previous_claims (customer_id, policy_id, claim_date, claim_amount,
 incident_type, incident_severity) VALUES
 ('C1001', 'P1001', '2025-06-01', 5000, 'Single Vehicle Collision', 'Minor Damage'),
 ('C1002', 'P1002', '2025-07-01', 4000, 'Single Vehicle Collision', 'Minor Damage');
INSERT INTO claims (claim_id, customer_id, policy_id, incident_date, incident_type,
 collision_type, incident_severity, authorities_contacted, incident_state,
 incident_city, incident_hour_of_the_day, incident_location,
 number_of_vehicles_involved, property_damage, bodily_injuries, witnesses,
 police_report_available, total_claim_amount, claim_description, status) VALUES
 ('CLM-DEMO-001', 'C1001', 'P1001', '2026-06-01', 'Single Vehicle Collision',
  'Front Collision', 'Minor Damage', 'Police', 'OH', 'Columbus', 10,
  'Fictional demo road', 1, false, 0, 1, true, 10000,
  'Demo incident: the vehicle struck a divider while turning.', 'submitted'),
 ('CLM-DEMO-002', 'C1002', 'P1002', '2026-06-02', 'Single Vehicle Collision',
  'Rear Collision', 'Minor Damage', 'Police', 'OH', 'Columbus', 12,
  'Fictional demo parking area', 1, false, 0, 1, true, 8000,
  'Demo incident: the vehicle reversed into a stationary barrier.', 'submitted');
COMMIT;

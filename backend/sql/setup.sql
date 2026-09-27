-- Fresh, empty databases ONLY. Run with psql -v ON_ERROR_STOP=1.
-- Generated from current SQLAlchemy metadata; no credentials or existing-data changes.
-- Alembic owns claim_history and users. Python-side defaults are not SQL defaults.
BEGIN;

CREATE TABLE claim_analyses (
	analysis_id VARCHAR(50) NOT NULL,
	claim_id VARCHAR(50) NOT NULL,
	fraud_analysis JSONB NOT NULL,
	nlp_analysis JSONB NOT NULL,
	policy_checks JSONB NOT NULL,
	policy_analysis JSONB NOT NULL,
	created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL,
	PRIMARY KEY (analysis_id)
);

CREATE INDEX ix_claim_analyses_claim_id ON claim_analyses (claim_id);

CREATE TABLE customers (
	customer_id VARCHAR(50) NOT NULL,
	name VARCHAR NOT NULL,
	date_of_birth DATE NOT NULL,
	sex VARCHAR NOT NULL,
	education_level VARCHAR NOT NULL,
	occupation VARCHAR NOT NULL,
	hobbies VARCHAR NOT NULL,
	relationship VARCHAR NOT NULL,
	zip_code VARCHAR NOT NULL,
	PRIMARY KEY (customer_id)
);

CREATE TABLE policies (
	policy_id VARCHAR(50) NOT NULL,
	customer_id VARCHAR(50) NOT NULL,
	policy_number VARCHAR NOT NULL,
	policy_bind_date DATE NOT NULL,
	policy_state VARCHAR NOT NULL,
	policy_csl VARCHAR NOT NULL,
	deductible NUMERIC NOT NULL,
	annual_premium NUMERIC NOT NULL,
	umbrella_limit NUMERIC NOT NULL,
	policy_end_date DATE,
	policy_status VARCHAR(20) NOT NULL,
	product_code VARCHAR(50),
	coverage_limit NUMERIC(12, 2),
	PRIMARY KEY (policy_id),
	FOREIGN KEY(customer_id) REFERENCES customers (customer_id)
);

CREATE INDEX ix_policies_customer_id ON policies (customer_id);

CREATE TABLE claims (
	claim_id VARCHAR(20) NOT NULL,
	customer_id VARCHAR(50) NOT NULL,
	policy_id VARCHAR(50) NOT NULL,
	incident_date DATE NOT NULL,
	incident_type VARCHAR NOT NULL,
	collision_type VARCHAR,
	incident_severity VARCHAR(50),
	authorities_contacted VARCHAR(50),
	incident_state VARCHAR(50),
	incident_city VARCHAR(100),
	incident_hour_of_the_day INTEGER,
	incident_location VARCHAR NOT NULL,
	number_of_vehicles_involved INTEGER NOT NULL,
	property_damage BOOLEAN,
	bodily_injuries INTEGER NOT NULL,
	witnesses INTEGER NOT NULL,
	police_report_available BOOLEAN,
	total_claim_amount NUMERIC NOT NULL,
	claim_description TEXT NOT NULL,
	status VARCHAR NOT NULL,
	created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT now() NOT NULL,
	PRIMARY KEY (claim_id),
	FOREIGN KEY(customer_id) REFERENCES customers (customer_id),
	FOREIGN KEY(policy_id) REFERENCES policies (policy_id)
);

CREATE INDEX ix_claims_customer_id ON claims (customer_id);

CREATE INDEX ix_claims_policy_id ON claims (policy_id);

CREATE TABLE previous_claims (
	previous_claim_id SERIAL NOT NULL,
	customer_id VARCHAR(50) NOT NULL,
	policy_id VARCHAR(50) NOT NULL,
	claim_date DATE NOT NULL,
	claim_amount NUMERIC NOT NULL,
	incident_type VARCHAR NOT NULL,
	incident_severity VARCHAR NOT NULL,
	PRIMARY KEY (previous_claim_id),
	FOREIGN KEY(customer_id) REFERENCES customers (customer_id),
	FOREIGN KEY(policy_id) REFERENCES policies (policy_id)
);

CREATE INDEX ix_previous_claims_customer_id ON previous_claims (customer_id);

CREATE INDEX ix_previous_claims_policy_id ON previous_claims (policy_id);

CREATE TABLE vehicles (
	vehicle_id SERIAL NOT NULL,
	customer_id VARCHAR(50) NOT NULL,
	policy_id VARCHAR(50) NOT NULL,
	make VARCHAR NOT NULL,
	model VARCHAR NOT NULL,
	year INTEGER NOT NULL,
	PRIMARY KEY (vehicle_id),
	FOREIGN KEY(customer_id) REFERENCES customers (customer_id),
	FOREIGN KEY(policy_id) REFERENCES policies (policy_id)
);

CREATE INDEX ix_vehicles_customer_id ON vehicles (customer_id);

CREATE INDEX ix_vehicles_policy_id ON vehicles (policy_id);

COMMIT;

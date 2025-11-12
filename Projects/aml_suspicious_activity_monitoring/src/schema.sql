CREATE TABLE clients (
  client_id INTEGER PRIMARY KEY,
  client_name VARCHAR,
  residency_country VARCHAR(4),
  pep_flag INTEGER,
  birth_year INTEGER,
  onboard_date DATE,
  occupation VARCHAR,
  source_of_funds VARCHAR,
  starting_balance_usd NUMERIC(18,2)
);

CREATE TABLE transactions (
  tx_id INTEGER PRIMARY KEY,
  client_id INTEGER REFERENCES clients(client_id),
  ts TIMESTAMP,
  amount_usd NUMERIC(18,2),
  currency VARCHAR(4),
  channel VARCHAR(16),
  tx_type VARCHAR(16),
  direction VARCHAR(8),
  counterparty_country VARCHAR(4),
  is_international INTEGER,
  label_suspicious_injected INTEGER
);

CREATE TABLE country_risk (
  country VARCHAR(4) PRIMARY KEY,
  risk_score INTEGER,
  is_high_risk INTEGER
);

CREATE INDEX idx_tx_client_ts ON transactions(client_id, ts);
CREATE INDEX idx_tx_counterparty ON transactions(counterparty_country);
CREATE INDEX idx_tx_channel ON transactions(channel);

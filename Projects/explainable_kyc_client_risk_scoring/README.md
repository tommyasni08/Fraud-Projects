# KYC Client Risk Scorecard (Mini-Module)

This module builds an **explainable KYC client risk score** by combining:

- Static KYC attributes (`clients.csv`)
- Transaction-derived behavioural features (`transactions.csv`)
- Country risk (`country_risk.csv`)
- Lightweight PEP/sanctions **watchlist enrichment**
- Simple data-quality checks

Outputs include a client-level risk score, risk tier (Low / Medium / High),
plain-English top factors, and watchlist flags.

Key components:
- `config.yaml` – score weights and thresholds
- `scorecard.py` – scoring logic + watchlist enrichment
- `data_quality.py` – basic data-quality checks
- `watchlist.csv` – synthetic PEP/sanctions reference
- `kyc_risk.sql` – example SQL for behaviour aggregation

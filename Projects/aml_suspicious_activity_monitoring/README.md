# 🕵️ AML Suspicious Activity Monitoring Dashboard

This project simulates an end-to-end **AML (Anti‑Money Laundering) analytics pipeline** similar to what a
Compliance or Risk Data Analyst would build in a financial institution.

---

## 🎯 Objectives

- Generate realistic synthetic datasets with injected suspicious behaviors.
- Build explainable, **rule‑based + ML hybrid detection** for anomalous transactions.
- Visualize insights interactively via a **Streamlit dashboard** for compliance review.

---

## 🧩 Structure

```
aml_suspicious_activity_monitoring/
├── data/                # synthetic datasets
├── src/                 # generator + feature + detection scripts
├── app.py               # Streamlit dashboard
├── main.py
├── README.md
└── .gitignore
```

---

## ⚙️ Usage

### 1️⃣ Generate Synthetic Data

```bash
python src/generate_synthetic_data.py   --outdir ./data   --clients 2000   --transactions 50000   --seed 42
```

### 2️⃣ Feature Engineering + Detection (Alternatively can run the main.py file)

```python
import pandas as pd
from src.feature_engineering import build_features
from src.detect_anomalies import apply_rules, isolation_forest_scores, combine_scores

tx = pd.read_csv("data/transactions.csv")
cr = pd.read_csv("data/country_risk.csv")
feats = build_features(tx, cr)
scored = apply_rules(feats)
scored["iforest_score"] = isolation_forest_scores(scored)
final = combine_scores(scored)
final.sort_values("hybrid_score", ascending=False).head(20)
```

### 3️⃣ Run Dashboard

```bash
pip install streamlit scikit-learn pandas numpy
streamlit run app.py
```

---

## 📊 Key Components

| Component                    | Description                                                                                                   |
| ---------------------------- | ------------------------------------------------------------------------------------------------------------- |
| **Synthetic Data Generator** | Creates client and transaction data with archetypes (high-value to HRC, rapid in/out, smurfing, etc.)         |
| **Feature Engineering**      | Rolling 1/7/30‑day counts and sums, high-risk country exposure, cash/SWIFT activity flags, z-score deviations |
| **Hybrid Detection**         | Weighted combination of rule-based logic + Isolation Forest scores                                            |
| **Streamlit Dashboard**      | Interactive view to filter and drill down flagged cases                                                       |

---

## 🧾 SQL Schema

A ready-to-use schema is in `src/schema.sql` (Postgres/Snowflake syntax).

---

## ⚠️ Disclaimer

All data is synthetic and for educational use only.

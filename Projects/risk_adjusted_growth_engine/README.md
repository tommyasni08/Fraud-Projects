# RAGE — Risk-Adjusted Growth Engine

Goal: Demonstrate how a fintech platform can increase product growth (deposits & trading activity) while managing fraud and abuse risk using machine learning, uplift modeling, and constrained optimization.

## 🚀 Project Overview

This project simulates a realistic growth–risk trade-off faced by fintech apps like Pluang, Revolut, or Robinhood.
It builds an end-to-end analytics & machine learning pipeline that:

1. Generates synthetic fintech user data
2. Builds predictive models for deposit uplift and fraud risk
3. Optimizes marketing actions under risk and budget constraints
4. Outputs actionable policy recommendations for safer, data-driven growth

## 🧩 Pipeline Architecture

| Step                       | Module                                         | Description                                                                 | Deliverables                                  |
| -------------------------- | ---------------------------------------------- | --------------------------------------------------------------------------- | --------------------------------------------- |
| **1. Data Simulation**     | `src/simulate/generate_data.py`                | Create synthetic fintech users, transactions, campaigns, and fraud patterns | `data/raw/` CSVs                              |
| **2. Feature Engineering** | `src/features/build_features.py`               | Compute rolling & lagged behavior features and guardrails                   | `data/processed/features_user_week.csv`       |
| **3. Modeling**            | `src/models/train_uplift.py` & `train_risk.py` | Predict expected net revenue per arm and blended risk score                 | `artifacts/models/*.pkl`, `predictions/*.csv` |
| **4. Policy Optimization** | `src/policy/optimize_policy.py`                | Choose optimal marketing treatment under constraints                        | `artifacts/policy_report.json`                |

## 📊 Business Scenario

Context:
Fintech company wants to boost user investment activity via personalized campaigns:
| Arm | Treatment | Cost | Expected Impact | Risk |
| ------------------ | ------------------------- | ---- | --------------- | ------ |
| Control | No promo | 0 | Baseline | Low |
| Education Nudge | In-app tutorial | 0 | Medium | Low |
| Personalized Reco | Portfolio recommendation | 0 | High | Medium |
| Reco + Small Bonus | Recommendation + cashback | 0.5 | Very High | High |

The challenge is to **maximize revenue uplift** while **keeping fraud** and **bonus abuse under control**.

## ⚙️ Modeling Strategy

1. **Uplift Modeling**

- **Goal**: Predict incremental revenue (`net_revenue`) due to each campaign.
- **Approach**: **Multi-arm T-Learner** (GradientBoostingRegressor per treatment arm).
- **Outputs**: Expected revenue per arm (`yhat_arm`), uplift vs. control.

2. **Risk Modeling**

- **Goal**: Estimate probability of fraud or abuse (`risk_blend`).
- **Approach**:
  - **RandomForestClassifier** for labeled fraud/abuse
  - **IsolationForest** for anomaly detection
  - Combine as weighted blend → `risk_blend = 0.7 * supervised + 0.3 * anomaly`

3. **Policy Optimization**

- **Goal**: Select the best campaign per user while controlling global risk and cost.
- **Formula**: Utility = yhat\_{arm} - λ_risk \* risk_blend - bonus_cost
- **Constraints**
  - Avg risk ≤ 8%
  - Avg bonus ≤ 0.5
- **Approach**: Greedy + repair loop under guardrails.

## 🧠 Technical Highlights

| Technique                               | Why It Matters                                                         |
| --------------------------------------- | ---------------------------------------------------------------------- |
| **Uplift Modeling (Causal ML)**         | Targets _incremental_ behavior change, not just conversion probability |
| **Hybrid Risk Stack (XGB + IsoForest)** | Captures both known and emerging fraud                                 |
| **Constrained Optimization**            | Balances growth vs. risk — real-world fintech decision logic           |
| **Fully Synthetic, Reproducible Data**  | 100% safe to share, but realistic patterns                             |
| **Modular, Runnable Scripts**           | Clean reproducibility: simulate → feature → model → optimize           |

## 🧰 How to Run Locally

```
# 1. Generate data
python rage/src/simulate/generate_data.py --output rage/data/raw --users 10000 --weeks 12 --seed 42

# 2. Build features
python rage/src/features/build_features.py --raw rage/data/raw --out rage/data/processed --min_weeks 2

# 3. Train uplift & risk models
python rage/src/models/train_uplift.py --features rage/data/processed/features_user_week.csv --out rage/artifacts
python rage/src/models/train_risk.py   --features rage/data/processed/features_user_week.csv --out rage/artifacts

# 4. Optimize campaign policy
python rage/src/policy/optimize_policy.py \
  --features rage/data/processed/features_user_week.csv \
  --uplift   rage/artifacts/predictions/uplift_predictions.csv \
  --risk     rage/artifacts/predictions/risk_scores.csv \
  --out      rage/artifacts
```

## 📁 Folder Structure

```
rage/
├── src/
│   ├── simulate/        # Synthetic data generator
│   ├── features/        # Feature builder & lag computation
|   ├── metrics/         # (Optional) uplift model metrics evaluation
│   ├── models/          # Uplift & risk training + evaluation
│   └── policy/          # Risk-adjusted optimization
├── data/
│   ├── raw/
│   └── processed/
├── artifacts/
│   ├── models/
│   ├── predictions/
│   ├── policy_report.json
│   ├── uplift_training_report.json
│   └── risk_training_report.json
├── configs/
│   ├── metrics.yaml
│   └── sim.yaml
└── README.md

```

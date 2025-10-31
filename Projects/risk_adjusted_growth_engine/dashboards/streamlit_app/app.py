import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
from pathlib import Path
import json

def load_artifacts(base_dir: Path):
    """Load processed features, policy recommendations, and the policy report."""
    artifacts = base_dir / "artifacts"
    data_dir = base_dir / "data" / "processed"
    features_path = data_dir / "features_user_week.csv"
    policy_path = artifacts / "predictions" / "policy_recommendations.csv"
    policy_report = artifacts / "policy_report.json"

    feat = pd.read_csv(features_path) if features_path.exists() else pd.DataFrame()
    pol = pd.read_csv(policy_path) if policy_path.exists() else pd.DataFrame()
    rep = json.load(open(policy_report)) if policy_report.exists() else {}
    return feat, pol, rep

def compute_kpis(feat: pd.DataFrame):
    """Business KPIs for the top tiles."""
    if feat.empty:
        return {"deposit_rate": 0.0, "avg_rev": 0.0, "fraud_loss_pct": 0.0}
    dep_rate = float((feat.get("deposit_success_amt", 0) > 0).mean() * 100)
    avg_rev = float(feat.get("net_revenue", 0).mean())
    num = float(feat.get("loss_fraud", 0).sum())
    den = float(feat.get("net_revenue", 0).sum())
    fraud_loss_pct = float((num / den * 100) if den != 0 else 0.0)
    return {"deposit_rate": dep_rate, "avg_rev": avg_rev, "fraud_loss_pct": fraud_loss_pct}

st.set_page_config(page_title="RAGE Control Tower", layout="wide")
st.title("💹 RAGE — Risk-Adjusted Growth Engine (Control Tower)")
st.caption("Executive analytics for growth vs. risk trade-offs in a fintech app.")

# repo base (rage/)
BASE = Path(__file__).resolve().parents[2]
feat, policy, report = load_artifacts(BASE)

# --- KPI tiles
st.subheader("📊 KPI Summary")
kpis = compute_kpis(feat)
c1, c2, c3 = st.columns(3)
c1.metric("Deposit Conversion %", f"{kpis['deposit_rate']:.2f}%")
c2.metric("Avg Revenue / User", f"${kpis['avg_rev']:.2f}")
c3.metric("Fraud Loss %", f"{kpis['fraud_loss_pct']:.2f}%")

# --- Policy distribution
st.subheader("🎯 Policy Distribution by Arm")
if not policy.empty:
    arm_counts = policy["arm_choice"].value_counts(normalize=True).mul(100).reset_index()
    arm_counts.columns = ["Arm", "% Users"]
    fig = px.bar(arm_counts, x="Arm", y="% Users", text="% Users")
    st.plotly_chart(fig, use_container_width=True)
else:
    st.info("No policy_recommendations found. Run the policy optimizer to populate artifacts.")

# --- Risk vs Reward frontier
st.subheader("⚖️ Risk vs Reward Frontier")
if not policy.empty:
    revenue_cols = [c for c in policy.columns if c.startswith("yhat_")]
    if revenue_cols:
        rewards = policy[revenue_cols].mean(axis=1)
        fig2 = px.scatter(
            policy, x="risk_blend", y=rewards,
            color="arm_choice",
            labels={"risk_blend": "Risk Score", "y": "Expected Revenue"},
            title="Risk vs Reward Frontier (per assigned arm)"
        )
        st.plotly_chart(fig2, use_container_width=True)
    else:
        st.info("No yhat_* columns found in policy predictions to plot reward.")
else:
    st.info("No policy data yet.")

# --- Report + scenario controls
st.subheader("🧾 Current Policy Report")
if report:
    st.json(report, expanded=False)
else:
    st.info("policy_report.json not found.")

st.subheader("🔧 Scenario Controls (What-If)")
lambda_risk = st.slider("λ_risk (risk penalty)", 0.5, 5.0, 2.0, 0.1)
max_risk = st.slider("Max Avg Risk", 0.02, 0.20, 0.08, 0.01)
max_bonus = st.slider("Max Avg Bonus", 0.1, 1.0, 0.5, 0.1)
st.caption("Tune these, then re-run optimize_policy.py with matching parameters to refresh artifacts.")

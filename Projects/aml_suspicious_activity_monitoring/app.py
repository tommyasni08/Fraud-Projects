import streamlit as st
import pandas as pd
import numpy as np
from pathlib import Path

st.set_page_config(page_title="AML Suspicious Activity Monitor", layout="wide")

DATA_DIR = Path("data")
TX_PATH = DATA_DIR/"transactions.csv"
CR_PATH = DATA_DIR/"country_risk.csv"

st.title("🚨 AML Suspicious Activity Monitor")

@st.cache_data
def load_data():
    tx = pd.read_csv(TX_PATH)
    cr = pd.read_csv(CR_PATH)
    return tx, cr

tx, cr = load_data()

# Load feature & detection utilities from local src
import importlib.util, sys
def import_from_path(module_name, path):
    spec = importlib.util.spec_from_file_location(module_name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod

feats_mod = import_from_path("feature_engineering", "src/feature_engineering.py")
detect_mod = import_from_path("detect_anomalies", "src/detect_anomalies.py")

with st.spinner("Building features & computing anomaly scores..."):
    feats = feats_mod.build_features(tx, cr)
    scored = detect_mod.apply_rules(feats)
    scored["iforest_score"] = detect_mod.isolation_forest_scores(scored)
    df = detect_mod.combine_scores(scored)

st.sidebar.header("Filters & Thresholds")
k = st.sidebar.slider("Top K rows", min_value=10, max_value=500, value=100, step=10)
min_rule = st.sidebar.slider("Min Rule Score", 0.0, 10.0, 0.0, 0.5)
min_ifor = st.sidebar.slider("Min IsolationForest Score", 0.0, 2.5, 0.0, 0.05)
alpha = st.sidebar.slider("Hybrid weight (model vs rules)", 0.0, 1.0, 0.6, 0.05)

# Recompute hybrid if alpha changed
df["hybrid_score"] = alpha*df["iforest_score"] + (1-alpha)*df["rule_score"]

# Column filters
countries = sorted(df["counterparty_country"].dropna().unique().tolist())
sel_countries = st.sidebar.multiselect("Counterparty Countries", countries, default=[])

channels = sorted(df["channel"].dropna().unique().tolist())
sel_channels = st.sidebar.multiselect("Channels", channels, default=[])

directions = sorted(df["direction"].dropna().unique().tolist())
sel_dirs = st.sidebar.multiselect("Direction", directions, default=[])

filtered = df.copy()
if sel_countries:
    filtered = filtered[filtered["counterparty_country"].isin(sel_countries)]
if sel_channels:
    filtered = filtered[filtered["channel"].isin(sel_channels)]
if sel_dirs:
    filtered = filtered[filtered["direction"].isin(sel_dirs)]

filtered = filtered[(filtered["rule_score"] >= min_rule) & (filtered["iforest_score"] >= min_ifor)]
top = filtered.sort_values("hybrid_score", ascending=False).head(k)

st.subheader("Top Flagged Transactions")
show_cols = ["tx_id","client_id","ts","amount_usd","channel","direction","counterparty_country",
             "rule_score","iforest_score","hybrid_score","label_suspicious_injected"]
st.dataframe(top[show_cols], use_container_width=True)

# Client profile drilldown
st.subheader("Client Profile")
cid = st.selectbox("Select Client ID", sorted(df["client_id"].unique().tolist()))
client_df = df[df["client_id"]==cid].sort_values("ts")
col1, col2, col3 = st.columns(3)
col1.metric("Tx count (30D)", int(client_df["roll_cnt_30D"].tail(1).values[0]))
col1.metric("Avg Tx (30D)", int(client_df["roll_cnt_30D"].mean()))
col2.metric("HRC Tx (30D)", int(client_df["roll_hrc_cnt_30D"].tail(1).values[0]))
col2.metric("Max HRC Tx (30D)", int(client_df["roll_hrc_cnt_30D"].max()))
col3.metric("Cash Tx (7D)", int(client_df["roll_cash_cnt_7D"].tail(1).values[0]))

st.line_chart(client_df.set_index("ts")[["amount_usd"]])
st.bar_chart(client_df["counterparty_country"].value_counts())

# Download case file
st.subheader("Export Case File")
dl = top[show_cols].to_csv(index=False).encode()
st.download_button("Download CSV (Top K)", data=dl, file_name="aml_top_flags.csv", mime="text/csv")

st.caption("Note: 'label_suspicious_injected' exists for validation in this synthetic dataset. In real settings, avoid training with it and treat it as post-hoc reference only.")

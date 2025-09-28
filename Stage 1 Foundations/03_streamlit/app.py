import streamlit as st
import pandas as pd
import os
from pathlib import Path

@st.cache_data
def load_data(transactions_path, chargebacks_path):
    tx = pd.read_csv(transactions_path, parse_dates=['timestamp'])
    cb = pd.read_csv(chargebacks_path)
    return tx, cb

# Streamlit Page Configuration
st.set_page_config(page_title="Chargeback Analytics", layout="wide")
st.title("Chargeback Analytics")
st.caption("Streamlit dashboard for chargeback trends & KPIs")

# Sidebar Configuration
st.sidebar.header('Filters')
date_range = st.sidebar.date_input("Date Range (set after data loads)", disabled=True)
payment_method = st.sidebar.multiselect("Payment Methods", [])
amount_sel = st.sidebar.slider("Amount Range", 0.0, 1000.0, (0.0, 1000.0))
granularity = st.sidebar.radio("Granularity", ["Day", "Week"])

st.info("✅ App scaffold loaded. Proceed to Step 1: Load data.")

# --- Load Data with Fallback Upload ---
APP_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = APP_DIR / "data"
tx_path = DATA_DIR / "transactions.csv"
cb_path = DATA_DIR / "chargebacks.csv"

if not tx_path.exists() or not cb_path.exists():
    st.warning("Local CSVs not found. Upload files below.")
    utx = st.file_uploader("Upload transactions.csv", type="csv")
    ucb = st.file_uploader("Upload chargebacks.csv", type="csv")
    if utx and ucb:
        tx, cb = load_data(utx, ucb)
    else:
        st.stop()
else:
    tx, cb = load_data(tx_path, cb_path)

## Types 
tx['timestamp'] = pd.to_datetime(tx['timestamp'], utc=True).dt.tz_convert(None)
tx['is_fraud'] = pd.to_numeric(tx['is_fraud'], errors='coerce').fillna(0).astype(int)

## Validatation
required_tx = {'transaction_id','user_id','timestamp','amount','payment_method','is_fraud'}
required_cb = {'transaction_id','user_id','amount','days_after_purchase'}

missing_tx = required_tx - set(tx.columns)
missing_cb = required_cb - set(cb.columns)

if missing_tx or missing_cb:
    st.error(f"Transactions missing columns: {missing_tx}")
    st.error(f"Chargebacks missing columns: {missing_cb}")
    st.stop()
    
with st.expander("Peek at data"):
    st.write("Transactions sample:", tx.head())
    st.write("Chargebacks sample:", cb.head())

with st.expander("About"):
    st.markdown("""
    - Track chargeback **count**, **rate**, and **$** over time  
    - Slice by **payment method** and **amount**  
    - See **time-to-chargeback** distribution  
    """)

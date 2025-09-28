import streamlit as st
import pandas as pd
import os
from pathlib import Path

# Streamlit Page Configuration
st.set_page_config(page_title="Chargeback Analytics", layout="wide")
st.title("Chargeback Analytics")
st.caption("Streamlit dashboard for chargeback trends & KPIs")

# Functions
@st.cache_data
def load_data(transactions_path, chargebacks_path):
    tx = pd.read_csv(transactions_path, parse_dates=['timestamp'])
    cb = pd.read_csv(chargebacks_path)
    return tx, cb

@st.cache_data
def prepare_views(tx, cb):
    ### Joined tx and cb
    df = tx.merge(cb[['transaction_id','amount','days_after_purchase']], on='transaction_id', how='left', suffixes=('','_cb'), indicator=True)
    df['is_chargeback'] = (df['_merge'] =='both').astype(int)
    df.drop(columns=['_merge'], inplace=True)
    ### Date buckets
    df['date'] = df['timestamp'].dt.floor('D')
    df['week_start']= df['timestamp'].dt.to_period('W').apply(lambda x: x.start_time)
    ## Aggregation
    daily = df.groupby('date').agg(
        tx_total=('transaction_id','count'),
        cb_count=('is_chargeback','sum')
    ).reset_index()
    daily['cb_rate'] = daily['cb_count'] / daily['tx_total'].replace(0, pd.NA)

    weekly = df.groupby('week_start').agg(
        tx_total=('transaction_id','count'),
        cb_count=('is_chargeback','sum')
    ).reset_index()
    weekly['cb_rate'] = weekly['cb_count'] / weekly['tx_total'].replace(0, pd.NA)
    return df, daily, weekly

def fmt_pct(x): return f"{x:.2%}"

def fmt_cur(x): return f"${x:,.2f}"

@st.cache_data
def compute_kpi(df_filt):
    total_tx  = len(df_filt)
    cb_count  = int(df_filt['is_chargeback'].sum())
    cb_rate   = (cb_count / total_tx) if total_tx else 0.0
    cb_sum    = float(df_filt.loc[df_filt['is_chargeback']==1, 'amount_cb'].sum())
    cb_avg    = float(df_filt.loc[df_filt['is_chargeback']==1, 'amount_cb'].mean() or 0.0)
    return cb_count, cb_rate, cb_sum, cb_avg

# Load Data with Fallback Upload
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

## Prepare Views
df, daily, weekly = prepare_views(tx,cb)

## Validatation
required_tx = {'transaction_id','user_id','timestamp','amount','payment_method','is_fraud'}
required_cb = {'transaction_id','user_id','amount','days_after_purchase'}

missing_tx = required_tx - set(tx.columns)
missing_cb = required_cb - set(cb.columns)

if missing_tx: st.error(f"Transactions missing columns: {missing_tx}")
if missing_cb: st.error(f"Chargebacks missing columns: {missing_cb}")
if missing_tx or missing_cb: st.stop()

# Sidebar Configuration
date_min = df['date'].min().date()  
date_max = df['date'].max().date()
methods  = sorted(df['payment_method'].dropna().unique().tolist())

amt_q01  = float(tx['amount'].quantile(0.01))
amt_q99  = float(tx['amount'].quantile(0.99))
amt_min, amt_max = float(tx['amount'].min()), float(tx['amount'].max())

with st.sidebar:
    st.header("Filters")
    date_range = st.date_input("Date Range", (date_min, date_max)) 
    method_sel = st.multiselect("Payment Methods", methods, default=methods)
    amount_sel = st.slider("Amount Range", min_value=amt_q01, max_value=amt_q99, value=(amt_q01, amt_q99))
    granularity = st.radio("Granularity", ["Day", "Week"], index=1)

# Apply Filters
if not isinstance(date_range, (list, tuple)) or len(date_range) == 1:
    start = end = pd.to_datetime(date_range if not isinstance(date_range,(list,tuple)) else date_range[0])
else:
    start, end = map(pd.to_datetime, date_range)
mask = (df['date'] >= start) & (df['date'] <= end)

if method_sel:
    mask &= df['payment_method'].isin(method_sel)

mask &= (df['amount'] >= amount_sel[0]) & (df['amount'] <= amount_sel[1])

df_filt = df.loc[mask].copy()
if df_filt.empty:
    st.warning("No data for the current filter selection.")
    st.stop()


# Dashboard Content
with st.expander("About"):
    st.markdown("""
    - Track chargeback **count**, **rate**, and **$** over time  
    - Slice by **payment method** and **amount**  
    - See **time-to-chargeback** distribution  
    """)

with st.expander("Peek at data"):
    st.write("Transactions sample:", tx.head())
    st.write("Chargebacks sample:", cb.head())
    st.write("Joined Data:", df.head())

st.success(f"Filtered rows: {len(df_filt):,} / {len(df):,}")

c1,c2,c3,c4 = st.columns(4)
cb_count, cb_rate, cb_sum, cb_avg = compute_kpi(df_filt)
c1.metric("Chargebacks", f"{cb_count:,}")
c2.metric("Chargeback Rate", fmt_pct(cb_rate))
c3.metric("Chargeback $ (Total)", fmt_cur(cb_sum))
c4.metric("Chargeback $ (Avg)", fmt_cur(cb_avg))
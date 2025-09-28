import streamlit as st
import pandas as pd
import os
from pathlib import Path
import plotly.graph_objects as go
from plotly.subplots import make_subplots

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
## Expanders (Intro and Data Peak)
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

## Filtered Row Count
st.success(f"Filtered rows: {len(df_filt):,} / {len(df):,}")

## KPI Tiles
c1,c2,c3,c4 = st.columns(4)
cb_count, cb_rate, cb_sum, cb_avg = compute_kpi(df_filt)
c1.metric("Chargebacks", f"{cb_count:,}")
c2.metric("Chargeback Rate", fmt_pct(cb_rate))
c3.metric("Chargeback $ (Total)", fmt_cur(cb_sum))
c4.metric("Chargeback $ (Avg)", fmt_cur(cb_avg))

## Trend Chart
if granularity == "Day":
    grp_col = 'date'
else:
    grp_col = 'week_start'

ts = (df_filt
      .groupby(grp_col)
      .agg(tx_total=('transaction_id','count'),
           cb_count=('is_chargeback','sum'))
      .reset_index()
     )
ts['cb_rate'] = ts['cb_count'] / ts['tx_total'].replace(0, pd.NA)

fig = go.Figure()

fig = make_subplots(specs=[[{"secondary_y": True}]])

fig.add_bar(x=ts[grp_col], y=ts['cb_count'], name='Chargebacks')
fig.add_trace(go.Scatter(x=ts[grp_col], y=ts['cb_rate'], mode='lines+markers', name='CB Rate'),
              secondary_y=True)

fig.update_layout(title=f"Chargebacks & Rate by {granularity}",
                  bargap=0.2, hovermode="x unified")
fig.update_yaxes(title_text="Chargebacks", secondary_y=False)
fig.update_yaxes(title_text="CB Rate", tickformat=".1%", secondary_y=True)

if ts.empty:
    st.info("No data for selected filters.")
else:
    st.plotly_chart(fig, use_container_width=True)

## Payment Method Breakdown
pm = (df_filt
      .groupby('payment_method')
      .agg(tx_total=('transaction_id','count'),
           cb_count=('is_chargeback','sum'),
           cb_amount_sum=('amount_cb','sum'),
           cb_amount_avg=('amount_cb','mean'))
      .reset_index()
     )
pm['cb_rate'] = pm['cb_count'] / pm['tx_total'].replace(0, pd.NA)

pm_sorted = pm.sort_values('cb_rate', ascending=False)

fig_pm = go.Figure(go.Bar(x=pm_sorted['payment_method'],
                          y=pm_sorted['cb_rate'],
                          text=pm_sorted['cb_rate'].map(lambda v: f"{v:.1%}"),
                          textposition='outside',
                          name='CB Rate'))
fig_pm.update_layout(title="Chargeback Rate by Payment Method",
                     yaxis_tickformat=".0%", xaxis_title="Payment Method",
                     yaxis_title="CB Rate")
st.plotly_chart(fig_pm, use_container_width=True)

show = pm_sorted.copy()
show['cb_rate'] = show['cb_rate'].map(lambda v: f"{v:.2%}" if pd.notna(v) else "—")
show['cb_amount_sum'] = show['cb_amount_sum'].map(lambda x: f"${x:,.2f}")
show['cb_amount_avg'] = show['cb_amount_avg'].map(lambda x: f"${x:,.2f}")
st.dataframe(show, use_container_width=True)

csv = pm_sorted.to_csv(index=False).encode('utf-8')
st.download_button("Download payment-method breakdown (CSV)", data=csv, file_name="pm_breakdown.csv", mime="text/csv")

## Time-to-Chargeback (delay) distribution
### 1) Filter CB rows
df_cb = df_filt[df_filt['is_chargeback'] == 1].copy()
df_cb['days_after_purchase'] = pd.to_numeric(df_cb['days_after_purchase'], errors='coerce')
df_cb = df_cb[df_cb['days_after_purchase'] >= 0]

if df_cb.empty:
    st.info("No chargebacks in current filter.")
else:
    ### 2) Buckets
    bins = [0, 10, 30, 60, float('inf')]
    labels = ['0-10', '11-30', '31-60', '>60']
    df_cb['cb_delay_bucket'] = pd.cut(df_cb['days_after_purchase'], bins=bins, labels=labels, right=True, include_lowest=True)

    ### 3) Aggregate
    delay = (df_cb.groupby('cb_delay_bucket')
             .agg(cb_count=('transaction_id','count'),
                  cb_amount_sum=('amount_cb','sum'),
                  cb_amount_avg=('amount_cb','mean'))
             .reset_index())


    ### 4) Plot counts
    fig_delay = make_subplots(specs=[[{"secondary_y": True}]])
    fig_delay.add_bar(x=delay['cb_delay_bucket'], y=delay['cb_count'], name='Chargebacks')
    fig_delay.add_scatter(x=delay['cb_delay_bucket'], y=delay['cb_amount_avg'], name='Avg CB $', mode='lines+markers', secondary_y=True)
    fig_delay.update_yaxes(title_text="Count", secondary_y=False)
    fig_delay.update_yaxes(title_text="Avg CB $", secondary_y=True)
    
    fig_delay.update_layout(title="Time to Chargeback (days)", xaxis_title="Delay bucket", yaxis_title="Count")

    st.plotly_chart(fig_delay, use_container_width=True)

    show = delay.copy()
    show['cb_amount_sum'] = show['cb_amount_sum'].fillna(0).map(lambda x: f"${x:,.2f}")
    show['cb_amount_avg'] = show['cb_amount_avg'].fillna(0).map(lambda x: f"${x:,.2f}")
    st.dataframe(show, use_container_width=True)

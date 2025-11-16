import pathlib
from typing import List, Tuple

import numpy as np
import pandas as pd
import streamlit as st

# -------------------------------------------------------------------
# CONFIG
# -------------------------------------------------------------------
BASE_DIR = pathlib.Path(__file__).resolve().parents[1]
PROCESSED_PATH = BASE_DIR / "data" / "processed" / "daily_risk_metrics_with_anomalies.csv"
TXN_PATH = BASE_DIR / "data" / "raw" / "transactions.csv"
USERS_PATH = BASE_DIR / "data" / "raw" / "users.csv"

DATE_COL = "txn_date"

CORE_METRICS = [
    "fraud_loss_amount",
    "fraud_txn_rate",
    "multi_account_device_rate",
    "failed_login_rate",
    "merchant_dispute_rate",
    "topup_failure_rate",
    "kyc_rejection_rate",
]


# -------------------------------------------------------------------
# DATA LOADERS
# -------------------------------------------------------------------
@st.cache_data
def load_daily_metrics() -> pd.DataFrame:
    df = pd.read_csv(PROCESSED_PATH)
    df[DATE_COL] = pd.to_datetime(df[DATE_COL])
    df = df.sort_values(DATE_COL)
    return df


@st.cache_data
def load_transactions() -> pd.DataFrame:
    df = pd.read_csv(TXN_PATH)
    df["txn_date"] = pd.to_datetime(df["txn_date"])
    df["txn_ts"] = pd.to_datetime(df["txn_ts"])
    return df


@st.cache_data
def load_users() -> pd.DataFrame:
    df = pd.read_csv(USERS_PATH)
    df["signup_date"] = pd.to_datetime(df["signup_date"])
    return df


# -------------------------------------------------------------------
# HELPERS
# -------------------------------------------------------------------
def latest_and_baseline(
    df: pd.DataFrame, metric: str, window: int = 7
) -> Tuple[pd.Timestamp, float, float]:
    """Return latest date value and mean of previous N days (excluding latest)."""
    if metric not in df.columns or df.empty:
        return None, np.nan, np.nan

    df = df.sort_values(DATE_COL)
    latest_date = df[DATE_COL].max()
    mask_hist = (df[DATE_COL] < latest_date) & (
        df[DATE_COL] >= latest_date - pd.Timedelta(days=window)
    )
    hist = df.loc[mask_hist, metric]

    latest_val = df.loc[df[DATE_COL] == latest_date, metric].iloc[0]
    baseline = hist.mean() if len(hist) > 0 else np.nan
    return latest_date, latest_val, baseline


def format_delta(cur: float, base: float, pct: bool = False) -> Tuple[str, str]:
    """Return delta label and direction string."""
    if np.isnan(cur) or np.isnan(base) or base == 0:
        return "n/a", "neutral"
    delta = (cur - base) / base
    value = f"{delta * 100:.1f}%" if pct else f"{delta:.2f}"
    direction = "flat"
    if delta > 0.1:
        direction = "up"
    elif delta < -0.1:
        direction = "down"
    signed = f"+{value}" if delta >= 0 else value
    return signed, direction


def build_risk_exposure_narrative(df: pd.DataFrame) -> List[str]:
    """
    Turn anomaly flags on the latest date into human-readable bullet points.
    """
    if df.empty:
        return []

    df = df.sort_values(DATE_COL)
    latest_date = df[DATE_COL].max()
    row = df[df[DATE_COL] == latest_date].iloc[0]

    bullets = []
    label_map = {
        "fraud_loss_amount": "Fraud loss amount",
        "fraud_txn_rate": "Fraud transaction rate",
        "multi_account_device_rate": "Multi-account device rate",
        "failed_login_rate": "Failed login rate",
        "merchant_dispute_rate": "Merchant dispute (chargeback) rate",
        "topup_failure_rate": "Top-up failure rate",
        "kyc_rejection_rate": "KYC rejection rate",
    }

    for metric in CORE_METRICS:
        flag_col = f"{metric}_is_anomaly"
        z_col = f"{metric}_zscore"
        delta_col = f"{metric}_delta_pct"

        if flag_col not in df.columns:
            continue
        if int(row.get(flag_col, 0)) != 1:
            continue

        cur = float(row[metric])
        base = df.loc[df[DATE_COL] < latest_date, metric].tail(7).mean()
        signed, direction = format_delta(cur, base, pct=True)
        z = row.get(z_col, np.nan)

        label = label_map.get(metric, metric)
        direction_word = {
            "up": "increased",
            "down": "decreased",
            "flat": "changed",
        }[direction]

        bullets.append(
            f"- **{label}** has {direction_word} vs the last 7 days average ({signed}; z-score ≈ {z:0.2f})."
        )

    return bullets


def apply_date_filter(df: pd.DataFrame, start_date, end_date) -> pd.DataFrame:
    if df.empty:
        return df
    mask = (df[DATE_COL].dt.date >= start_date) & (df[DATE_COL].dt.date <= end_date)
    return df.loc[mask].copy()


def apply_date_filter_txn(df: pd.DataFrame, start_date, end_date) -> pd.DataFrame:
    if df.empty:
        return df
    mask = (df["txn_date"].dt.date >= start_date) & (df["txn_date"].dt.date <= end_date)
    return df.loc[mask].copy()


# -------------------------------------------------------------------
# PAGES
# -------------------------------------------------------------------
def page_overview(daily: pd.DataFrame):
    st.markdown("### Overview")

    if daily.empty:
        st.info("No data available for the selected date range.")
        return

    latest_date = daily[DATE_COL].max()
    st.caption(f"Data up to: **{latest_date.date()}**")

    # KPI row
    kpi1, kpi2, kpi3, kpi4 = st.columns(4)

    # Fraud loss
    _, cur_loss, base_loss = latest_and_baseline(daily, "fraud_loss_amount")
    loss_delta, _ = format_delta(cur_loss, base_loss, pct=True)
    kpi1.metric(
        "Fraud loss (today)",
        f"{cur_loss:,.0f} SGD" if not np.isnan(cur_loss) else "n/a",
        loss_delta if loss_delta != "n/a" else None,
    )

    # Fraud txn rate
    _, cur_rate, base_rate = latest_and_baseline(daily, "fraud_txn_rate")
    rate_delta, _ = format_delta(cur_rate, base_rate, pct=True)
    kpi2.metric(
        "Fraud transaction rate",
        f"{cur_rate * 100:0.2f}%" if not np.isnan(cur_rate) else "n/a",
        rate_delta if rate_delta != "n/a" else None,
    )

    # Multi-account device rate
    _, cur_multi, base_multi = latest_and_baseline(daily, "multi_account_device_rate")
    multi_delta, _ = format_delta(cur_multi, base_multi, pct=True)
    kpi3.metric(
        "Multi-account device rate",
        f"{cur_multi * 100:0.2f}%" if not np.isnan(cur_multi) else "n/a",
        multi_delta if multi_delta != "n/a" else None,
    )

    # KYC rejection rate
    _, cur_kyc, base_kyc = latest_and_baseline(daily, "kyc_rejection_rate")
    kyc_delta, _ = format_delta(cur_kyc, base_kyc, pct=True)
    kpi4.metric(
        "KYC rejection rate",
        f"{cur_kyc * 100:0.2f}%" if not np.isnan(cur_kyc) else "n/a",
        kyc_delta if kyc_delta != "n/a" else None,
    )

    st.markdown("---")

    top_row = st.container()
    bottom_row = st.container()

    with top_row:
        left, right = st.columns([2, 1])

        with left:
            st.markdown("#### Fraud exposure over time")

            plot_df = daily[[DATE_COL, "fraud_loss_amount", "fraud_txn_rate"]].copy()
            plot_df = plot_df.sort_values(DATE_COL).set_index(DATE_COL)

            st.line_chart(plot_df[["fraud_loss_amount"]], height=220)
            st.caption("Daily fraud loss amount (SGD).")

            st.line_chart(plot_df[["fraud_txn_rate"]], height=220)
            st.caption("Daily fraud transaction rate.")

        with right:
            st.markdown("#### Risk exposure summary")

            bullets = build_risk_exposure_narrative(daily)
            if not bullets:
                st.success("No major anomalies vs the 7-day baseline on the latest date.")
            else:
                st.warning("Anomalies detected on the latest date:")
                for b in bullets:
                    st.markdown(b)

    with bottom_row:
        st.markdown("#### Operational volume")

        vol_df = daily[[DATE_COL, "total_txn_count", "total_txn_amount", "new_users"]].copy()
        vol_df = vol_df.sort_values(DATE_COL).set_index(DATE_COL)

        colA, colB = st.columns([1.3, 1])

        with colA:
            st.markdown("**Total transaction count**")
            st.line_chart(vol_df[["total_txn_count"]], height=200)

            st.markdown("**New users per day**")
            st.line_chart(vol_df[["new_users"]], height=200)

        with colB:
            st.markdown("**Total transaction amount (SGD)**")
            st.line_chart(vol_df[["total_txn_amount"]], height=420)
    
    st.caption(
        "Overall platform health: total transactions, total volume, and new user signups."
    )    

def page_anomalies(daily: pd.DataFrame):
    st.markdown("### Anomaly Explorer")

    if daily.empty:
        st.info("No data available for the selected date range.")
        return

    metric = st.selectbox(
        "Metric",
        options=CORE_METRICS,
        format_func=lambda x: {
            "fraud_loss_amount": "Fraud loss amount",
            "fraud_txn_rate": "Fraud transaction rate",
            "multi_account_device_rate": "Multi-account device rate",
            "failed_login_rate": "Failed login rate",
            "merchant_dispute_rate": "Merchant dispute rate",
            "topup_failure_rate": "Top-up failure rate",
            "kyc_rejection_rate": "KYC rejection rate",
        }.get(x, x),
    )

    metric_label = {
        "fraud_loss_amount": "Fraud loss amount (SGD)",
        "fraud_txn_rate": "Fraud transaction rate",
        "multi_account_device_rate": "Multi-account device rate",
        "failed_login_rate": "Failed login rate",
        "merchant_dispute_rate": "Merchant dispute rate",
        "topup_failure_rate": "Top-up failure rate",
        "kyc_rejection_rate": "KYC rejection rate",
    }.get(metric, metric)

    flag_col = f"{metric}_is_anomaly"
    z_col = f"{metric}_zscore"
    delta_col = f"{metric}_delta_pct"

    df = daily.sort_values(DATE_COL).copy()
    if metric not in df.columns:
        st.error(f"Metric '{metric}' not found in data.")
        return

    st.markdown(f"#### {metric_label}")
    chart_df = df[[DATE_COL, metric]].set_index(DATE_COL)
    st.line_chart(chart_df, height=280)

    st.caption("Time series for the selected metric.")

    if flag_col in df.columns:
        anomalies = df[df[flag_col] == 1].copy()
        st.markdown("#### Detected anomalies")
        if anomalies.empty:
            st.info("No anomalies flagged for this metric in the selected date range.")
        else:
            view_cols = [DATE_COL, metric]
            if z_col in df.columns:
                view_cols.append(z_col)
            if delta_col in df.columns:
                view_cols.append(delta_col)
            st.dataframe(
                anomalies[view_cols].sort_values(DATE_COL, ascending=False),
                use_container_width=True,
                hide_index=True,
            )
    else:
        st.info("No anomaly flag column found for this metric.")


def page_segment_drilldown(daily: pd.DataFrame, txns: pd.DataFrame, users: pd.DataFrame):
    st.markdown("### Segment Drilldown")

    if txns.empty:
        st.info("No transaction data in the selected date range.")
        return

    # Join user attributes into transaction table
    tx = txns.merge(
        users[["user_id", "country", "risk_segment"]],
        on="user_id",
        how="left",
        suffixes=("", "_user"),
    )

    segment_type = st.selectbox(
        "Segment by",
        options=["country", "risk_segment"],
        index=0,
    )

    metric_choice = st.selectbox(
        "Metric",
        options=["fraud_loss_amount", "fraud_txn_rate"],
        format_func=lambda x: {
            "fraud_loss_amount": "Fraud loss amount (SGD)",
            "fraud_txn_rate": "Fraud transaction rate",
        }.get(x, x),
    )

    latest_date = daily[DATE_COL].max()
    window = st.slider(
        "Baseline window (days before latest date)",
        min_value=7,
        max_value=30,
        value=14,
        step=1,
    )

    st.caption(
        f"Comparing latest date **{latest_date.date()}** against the previous **{window}** days."
    )

    tx["txn_date"] = pd.to_datetime(tx["txn_date"])
    mask_hist = (tx["txn_date"] < latest_date) & (
        tx["txn_date"] >= latest_date - pd.Timedelta(days=window)
    )
    tx_hist = tx[mask_hist]
    tx_latest = tx[tx["txn_date"] == latest_date]

    if metric_choice == "fraud_loss_amount":
        baseline_seg = (
            tx_hist[tx_hist["is_fraud_label"] == 1]
            .groupby(["txn_date", segment_type])["amount"]
            .sum()
            .groupby(level=1)
            .mean()
        )
        latest_seg = (
            tx_latest[tx_latest["is_fraud_label"] == 1]
            .groupby(segment_type)["amount"]
            .sum()
        )
    else:  # fraud_txn_rate
        def fraud_rate(group):
            total = len(group)
            if total == 0:
                return np.nan
            return group["is_fraud_label"].sum() / total

        baseline_seg = (
            tx_hist.groupby(["txn_date", segment_type])
            .apply(fraud_rate)
            .groupby(level=1)
            .mean()
        )
        latest_seg = tx_latest.groupby(segment_type).apply(fraud_rate)

    seg_df = pd.DataFrame(
        {
            "baseline": baseline_seg,
            "latest": latest_seg,
        }
    ).dropna()

    if seg_df.empty:
        st.info("No data available for this segment/metric/time window combination.")
        return

    seg_df["delta"] = seg_df["latest"] - seg_df["baseline"]
    seg_df["delta_pct"] = seg_df["delta"] / seg_df["baseline"].replace(0, np.nan)
    seg_df = seg_df.sort_values("delta_pct", ascending=False)

    st.markdown("#### Segment comparison")
    st.dataframe(
        seg_df.reset_index().rename(columns={segment_type: "segment"}),
        use_container_width=True,
        hide_index=True,
    )

    st.markdown("#### Top segments by relative increase")
    top_df = seg_df.sort_values("delta_pct", ascending=False).head(10)
    st.bar_chart(top_df[["delta_pct"]], height=280)
    st.caption("Segments where the risk metric has increased the most vs baseline.")


def page_raw_data(daily: pd.DataFrame, txns: pd.DataFrame):
    st.markdown("### Raw Data")

    tab1, tab2 = st.tabs(["Daily metrics", "Transactions sample"])

    with tab1:
        st.markdown("#### Daily risk metrics")
        st.dataframe(
            daily.sort_values(DATE_COL, ascending=False),
            use_container_width=True,
            hide_index=True,
        )

    with tab2:
        st.markdown("#### Transactions sample")
        if txns.empty:
            st.info("No transactions in the selected date range.")
        else:
            st.dataframe(
                txns.sample(min(500, len(txns))),
                use_container_width=True,
                hide_index=True,
            )


# -------------------------------------------------------------------
# MAIN APP
# -------------------------------------------------------------------
def main():
    st.set_page_config(
        page_title="Digital Wallet Fraud & Risk Dashboard",
        layout="wide",
        initial_sidebar_state="expanded",
    )

    # Load data
    daily = load_daily_metrics()
    txns = load_transactions()
    users = load_users()

    # SIDEBAR LAYOUT
    st.sidebar.markdown("### Digital Wallet Risk Console")
    st.sidebar.caption(
        "Synthetic environment for demonstrating anti-fraud & risk monitoring capabilities."
    )

    # Global date filter
    if not daily.empty:
        min_date = daily[DATE_COL].dt.date.min()
        max_date = daily[DATE_COL].dt.date.max()
        start_date, end_date = st.sidebar.date_input(
            "Date range",
            value=(min_date, max_date),
            min_value=min_date,
            max_value=max_date,
        )
        if isinstance(start_date, tuple):  # defensive, but streamlit returns tuple earlier versions
            start_date, end_date = start_date
        filtered_daily = apply_date_filter(daily, start_date, end_date)
        filtered_txns = apply_date_filter_txn(txns, start_date, end_date)
    else:
        filtered_daily = daily
        filtered_txns = txns

    st.sidebar.markdown("---")
    page = st.sidebar.radio(
        "View",
        options=["Overview", "Anomalies", "Segment Drilldown", "Raw Data"],
    )

    with st.container():
        st.markdown(
            """
            ## Digital Wallet Fraud & Risk Monitoring Dashboard
            <span style="font-size: 0.9rem; color: #777;">
            Synthetic data, real-world risk monitoring patterns. Built to mimic how fraud & risk teams track exposure in digital payments.
            </span>
            """,
            unsafe_allow_html=True,
        )

    st.markdown("---")

    if page == "Overview":
        page_overview(filtered_daily)
    elif page == "Anomalies":
        page_anomalies(filtered_daily)
    elif page == "Segment Drilldown":
        page_segment_drilldown(filtered_daily, filtered_txns, users)
    else:
        page_raw_data(filtered_daily, filtered_txns)


if __name__ == "__main__":
    main()

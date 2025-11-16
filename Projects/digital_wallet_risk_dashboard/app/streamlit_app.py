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

# metrics we care about most on overview/anomaly pages
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
    if metric not in df.columns:
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
    if delta > 0.1:
        direction = "up"
    elif delta < -0.1:
        direction = "down"
    else:
        direction = "flat"
    signed = f"+{value}" if delta >= 0 else value
    return signed, direction


def build_risk_exposure_narrative(df: pd.DataFrame) -> List[str]:
    """
    Turn anomaly flags on the latest date into human-readable bullet points.
    """
    df = df.sort_values(DATE_COL)
    latest_date = df[DATE_COL].max()
    row = df[df[DATE_COL] == latest_date].iloc[0]

    bullets = []
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
        delta_pct = row.get(delta_col, np.nan)

        label_map = {
            "fraud_loss_amount": "Fraud loss amount",
            "fraud_txn_rate": "Fraud transaction rate",
            "multi_account_device_rate": "Multi-account device rate",
            "failed_login_rate": "Failed login rate",
            "merchant_dispute_rate": "Merchant dispute (chargeback) rate",
            "topup_failure_rate": "Top-up failure rate",
            "kyc_rejection_rate": "KYC rejection rate",
        }
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


# -------------------------------------------------------------------
# PAGES
# -------------------------------------------------------------------
def page_overview(daily: pd.DataFrame):
    st.header("📊 Overview – Digital Wallet Fraud & Risk Monitoring")

    latest_date = daily[DATE_COL].max()
    st.caption(f"Data up to: **{latest_date.date()}**")

    col1, col2, col3, col4 = st.columns(4)

    # Card 1 – Fraud loss
    _, cur_loss, base_loss = latest_and_baseline(daily, "fraud_loss_amount")
    loss_delta, _ = format_delta(cur_loss, base_loss, pct=True)
    col1.metric(
        "Fraud loss (today)",
        f"{cur_loss:,.0f} SGD" if not np.isnan(cur_loss) else "n/a",
        loss_delta if loss_delta != "n/a" else None,
    )

    # Card 2 – Fraud txn rate
    _, cur_rate, base_rate = latest_and_baseline(daily, "fraud_txn_rate")
    rate_delta, _ = format_delta(cur_rate, base_rate, pct=True)
    col2.metric(
        "Fraud txn rate (today)",
        f"{cur_rate*100:0.2f}%" if not np.isnan(cur_rate) else "n/a",
        rate_delta if rate_delta != "n/a" else None,
    )

    # Card 3 – Multi-account device rate
    _, cur_multi, base_multi = latest_and_baseline(daily, "multi_account_device_rate")
    multi_delta, _ = format_delta(cur_multi, base_multi, pct=True)
    col3.metric(
        "Multi-account device rate",
        f"{cur_multi*100:0.2f}%" if not np.isnan(cur_multi) else "n/a",
        multi_delta if multi_delta != "n/a" else None,
    )

    # Card 4 – KYC rejection rate
    _, cur_kyc, base_kyc = latest_and_baseline(daily, "kyc_rejection_rate")
    kyc_delta, _ = format_delta(cur_kyc, base_kyc, pct=True)
    col4.metric(
        "KYC rejection rate",
        f"{cur_kyc*100:0.2f}%" if not np.isnan(cur_kyc) else "n/a",
        kyc_delta if kyc_delta != "n/a" else None,
    )

    st.markdown("---")

    col_left, col_right = st.columns([2, 1])

    with col_left:
        st.subheader("Fraud loss & fraud rate over time")
        plot_df = daily[[DATE_COL, "fraud_loss_amount", "fraud_txn_rate"]].copy()
        plot_df = plot_df.sort_values(DATE_COL)
        plot_df = plot_df.set_index(DATE_COL)

        st.line_chart(
            plot_df[["fraud_loss_amount"]],
            height=250,
        )
        st.caption("Fraud loss amount per day (SGD).")

        st.line_chart(
            plot_df[["fraud_txn_rate"]],
            height=250,
        )
        st.caption("Fraud transactions as a fraction of all transactions.")

    with col_right:
        st.subheader("Risk exposure summary")

        bullets = build_risk_exposure_narrative(daily)
        if not bullets:
            st.success("No major anomalies vs the 7-day baseline on the latest date.")
        else:
            st.warning("Anomalies detected for the latest date:")
            for b in bullets:
                st.markdown(b)

    st.markdown("---")

    st.subheader("Operational Volume")

    vol_df = daily[[DATE_COL, "total_txn_count", "total_txn_amount", "new_users"]].copy()
    vol_df = vol_df.sort_values(DATE_COL).set_index(DATE_COL)

    colA, colB = st.columns(2)

    with colA:
        st.markdown("**Total Transaction Count**")
        st.line_chart(vol_df[["total_txn_count"]], height=200)

        st.markdown("**New Users per Day**")
        st.line_chart(vol_df[["new_users"]], height=200)

    with colB:
        st.markdown("**Total Transaction Amount (SGD)**")
        st.line_chart(vol_df[["total_txn_amount"]], height=420)

    st.caption(
        "Overall platform health: total transactions, total volume, and new user signups."
    )


def page_anomalies(daily: pd.DataFrame):
    st.header("🚨 Anomaly Explorer")

    metric = st.selectbox(
        "Select metric to inspect",
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
        "fraud_txn_rate": "Fraud txn rate",
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

    st.subheader(metric_label)
    chart_df = df[[DATE_COL, metric]].set_index(DATE_COL)
    st.line_chart(chart_df, height=300)

    st.caption("Time series for the selected metric.")

    if flag_col in df.columns:
        anomalies = df[df[flag_col] == 1].copy()
        st.markdown("#### Detected anomalies (z-score ≥ 2 and |Δ| ≥ 30%)")
        if anomalies.empty:
            st.info("No anomalies flagged for this metric.")
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
    st.header("🔍 Segment Drilldown")

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
            "fraud_txn_rate": "Fraud txn rate",
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

    # compute segment metrics for baseline and latest
    # fraud loss amount per segment per day
    tx["txn_date"] = pd.to_datetime(tx["txn_date"])
    mask_hist = (tx["txn_date"] < latest_date) & (
        tx["txn_date"] >= latest_date - pd.Timedelta(days=window)
    )
    tx_hist = tx[mask_hist]
    tx_latest = tx[tx["txn_date"] == latest_date]

    # baseline: mean per day per segment
    if metric_choice == "fraud_loss_amount":
        baseline_seg = (
            tx_hist[tx_hist["is_fraud_label"] == 1]
            .groupby(["txn_date", segment_type])["amount"]
            .sum()
            .groupby(segment_type)
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

    st.subheader("Segment comparison table")
    st.dataframe(
        seg_df.reset_index().rename(columns={segment_type: "segment"}),
        use_container_width=True,
        hide_index=True,
    )

    st.subheader("Top segments by relative increase")
    plot_df = seg_df.copy()
    plot_df = plot_df.sort_values("delta_pct", ascending=False).head(10)
    st.bar_chart(
        plot_df[["delta_pct"]],
        height=300,
    )
    st.caption(
        "Top segments where risk metric has increased the most vs the baseline window."
    )


def page_raw_data(daily: pd.DataFrame, txns: pd.DataFrame):
    st.header("📁 Raw Data Preview")

    tab1, tab2 = st.tabs(["Daily metrics", "Transactions sample"])

    with tab1:
        st.subheader("Daily risk metrics (processed)")
        st.dataframe(daily.sort_values(DATE_COL, ascending=False), use_container_width=True)

    with tab2:
        st.subheader("Transactions sample")
        st.dataframe(
            txns.sample(min(500, len(txns))), use_container_width=True, hide_index=True
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

    st.sidebar.title("Navigation")
    page = st.sidebar.radio(
        "Go to",
        options=["Overview", "Anomalies", "Segment Drilldown", "Raw Data"],
    )

    with st.sidebar.expander("Project context", expanded=False):
        st.write(
            "Prototype risk monitoring dashboard for a digital wallet / payments platform. "
            "Data is synthetic, designed to mimic fraud & operational patterns for learning and portfolio purposes."
        )

    # load data
    daily = load_daily_metrics()
    txns = load_transactions()
    users = load_users()

    if page == "Overview":
        page_overview(daily)
    elif page == "Anomalies":
        page_anomalies(daily)
    elif page == "Segment Drilldown":
        page_segment_drilldown(daily, txns, users)
    else:
        page_raw_data(daily, txns)


if __name__ == "__main__":
    main()

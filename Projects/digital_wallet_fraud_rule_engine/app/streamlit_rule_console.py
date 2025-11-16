import pathlib

import numpy as np
import pandas as pd
import streamlit as st

# -------------------------------------------------------------------
# CONFIG
# -------------------------------------------------------------------
BASE_DIR = pathlib.Path(__file__).resolve().parents[1]
TXN_PATH = BASE_DIR / "data" / "transactions_with_scenarios.csv"
EVAL_PATH = BASE_DIR / "data" / "rule_evaluation_summary.csv"

RULE_COLUMNS = [
    "R1_velocity",
    "R2_cashout",
    "R3_device_farming",
    "R4_new_account_abuse",
    "R5_geo_anomaly",
]


# -------------------------------------------------------------------
# DATA LOADERS
# -------------------------------------------------------------------
@st.cache_data
def load_transactions() -> pd.DataFrame:
    df = pd.read_csv(TXN_PATH)
    df["txn_ts"] = pd.to_datetime(df["txn_ts"])
    df["txn_date"] = pd.to_datetime(df["txn_date"])
    return df


@st.cache_data
def load_rule_eval() -> pd.DataFrame:
    return pd.read_csv(EVAL_PATH)


# -------------------------------------------------------------------
# METRIC HELPERS
# -------------------------------------------------------------------
def compute_metrics(y_pred: np.ndarray, y_true: np.ndarray) -> dict:
    tp = int(((y_pred == 1) & (y_true == 1)).sum())
    fp = int(((y_pred == 1) & (y_true == 0)).sum())
    fn = int(((y_pred == 0) & (y_true == 1)).sum())
    tn = int(((y_pred == 0) & (y_true == 0)).sum())

    precision = tp / (tp + fp) if (tp + fp) > 0 else np.nan
    recall = tp / (tp + fn) if (tp + fn) > 0 else np.nan
    fpr = fp / (fp + tn) if (fp + tn) > 0 else np.nan
    tpr = recall

    return {
        "tp": tp,
        "fp": fp,
        "fn": fn,
        "tn": tn,
        "precision": precision,
        "recall": recall,
        "fpr": fpr,
        "tpr": tpr,
    }


def format_pct(x):
    if x is None or np.isnan(x):
        return "n/a"
    return f"{x*100:0.2f}%"


# -------------------------------------------------------------------
# UI COMPONENTS
# -------------------------------------------------------------------
def show_rule_summary_header(rule_name: str):
    st.markdown(f"### Rule tuning – `{rule_name}`")


def show_overall_context(tx: pd.DataFrame):
    total_tx = len(tx)
    fraud_rate = tx["is_fraud"].mean() if total_tx > 0 else np.nan

    c1, c2 = st.columns(2)
    c1.metric("Total transactions", f"{total_tx:,}")
    c2.metric("Fraud prevalence", format_pct(fraud_rate))


def show_confusion_matrix(metrics: dict):
    st.markdown("#### Confusion matrix")

    matrix_df = pd.DataFrame(
        [
            ["Actual fraud", metrics["tp"], metrics["fn"]],
            ["Actual normal", metrics["fp"], metrics["tn"]],
        ],
        columns=["", "Predicted fraud", "Predicted normal"],
    )
    st.table(matrix_df)


def show_rule_metrics(metrics: dict):
    c1, c2, c3 = st.columns(3)
    c1.metric("Precision", format_pct(metrics["precision"]))
    c2.metric("Recall (TPR)", format_pct(metrics["recall"]))
    c3.metric("False positive rate (FPR)", format_pct(metrics["fpr"]))


def show_flagged_distribution(tx: pd.DataFrame, y_pred: np.ndarray):
    tx = tx.copy()
    tx["is_flagged"] = y_pred
    fraud_rate_flagged = tx.loc[tx["is_flagged"] == 1, "is_fraud"].mean()
    fraud_rate_unflagged = tx.loc[tx["is_flagged"] == 0, "is_fraud"].mean()

    st.markdown("#### Fraud rate: flagged vs not flagged")
    dist_df = pd.DataFrame(
        {
            "group": ["Flagged", "Not flagged"],
            "fraud_rate": [fraud_rate_flagged, fraud_rate_unflagged],
        }
    )
    st.bar_chart(
        dist_df.set_index("group"),
        height=260,
    )
    st.caption("Fraud prevalence among flagged vs non-flagged transactions.")


def show_sample_transactions(tx: pd.DataFrame, y_pred: np.ndarray, title_suffix: str):
    tx = tx.copy()
    tx["is_flagged"] = y_pred

    st.markdown(f"#### Sample flagged transactions ({title_suffix})")

    flagged = tx[tx["is_flagged"] == 1].copy()
    if flagged.empty:
        st.info("No transactions flagged under current settings.")
        return

    # Pick columns that tell a fraud story
    cols = [
        "txn_id",
        "txn_ts",
        "user_id",
        "device_id",
        "country",
        "risk_segment",
        "txn_type",
        "amount",
        "fraud_scenario",
        "is_fraud",
    ]
    cols = [c for c in cols if c in flagged.columns]

    # Prioritize suspicious-looking transactions: fraud first, then high amount
    flagged = flagged.sort_values(["is_fraud", "amount"], ascending=[False, False])

    st.dataframe(
        flagged[cols].head(50),
        use_container_width=True,
        hide_index=True,
    )
    st.caption("Top 50 flagged transactions (fraud first, then largest amounts).")


def show_risk_score_distribution(tx: pd.DataFrame):
    st.markdown("#### Risk score distribution (fraud vs normal)")

    if "risk_score_rules" not in tx.columns:
        st.info("No `risk_score_rules` column found in transactions.")
        return

    # simple binned distribution per class
    bins = np.linspace(tx["risk_score_rules"].min(), tx["risk_score_rules"].max(), 20)
    tx["score_bin"] = pd.cut(tx["risk_score_rules"], bins=bins, include_lowest=True)

    dist = (
        tx.groupby(["score_bin", "is_fraud"])["txn_id"]
        .count()
        .reset_index(name="count")
    )
    # pivot for stacked-style view
    pivot = dist.pivot(index="score_bin", columns="is_fraud", values="count").fillna(0)
    pivot.columns = ["normal", "fraud"] if len(pivot.columns) == 2 else pivot.columns

    pivot.index = pivot.index.astype(str)
    st.bar_chart(pivot, height=260)
    st.caption("Higher scores should concentrate more fraud transactions if rules are effective.")


# -------------------------------------------------------------------
# MAIN PAGE LOGIC
# -------------------------------------------------------------------
def page_rule_console():
    st.set_page_config(
        page_title="Fraud Rule Tuning Console",
        layout="wide",
        initial_sidebar_state="expanded",
    )

    st.sidebar.markdown("### Rule Tuning Console")
    st.sidebar.caption(
        "Inspect and tune rule-based detections for synthetic digital wallet fraud scenarios."
    )

    tx = load_transactions()
    eval_df = load_rule_eval()

    show_overall_context(tx)

    st.markdown("---")

    # Rule selection
    rule_options = RULE_COLUMNS + ["ALL_RULES_COMBINED"]
    rule = st.sidebar.selectbox(
        "Rule",
        options=rule_options,
        index=len(RULE_COLUMNS),  # default to ALL_RULES_COMBINED
        format_func=lambda x: x if x != "ALL_RULES_COMBINED" else "All rules combined",
    )

    # For ALL_RULES_COMBINED, allow risk-score threshold tuning
    if rule == "ALL_RULES_COMBINED":
        show_rule_summary_header("ALL_RULES_COMBINED (risk_score_rules threshold)")

        if "risk_score_rules" not in tx.columns:
            st.error("`risk_score_rules` column not found. Did you run the simulation script?")
            return

        min_score = float(tx["risk_score_rules"].min())
        max_score = float(tx["risk_score_rules"].max())
        default_thr = 1.5 if (min_score <= 1.5 <= max_score) else (min_score + (max_score - min_score) / 3)

        threshold = st.sidebar.slider(
            "Risk score threshold",
            min_value=float(np.floor(min_score * 10) / 10),
            max_value=float(np.ceil(max_score * 10) / 10),
            value=float(default_thr),
            step=0.1,
        )

        st.markdown(
            f"Using **risk_score_rules ≥ {threshold:0.1f}** as the flagging threshold for the combined ruleset."
        )

        y_pred = (tx["risk_score_rules"].values >= threshold).astype(int)
        y_true = tx["is_fraud"].values

        metrics = compute_metrics(y_pred, y_true)

        # layout
        top_row = st.container()
        bottom_row = st.container()

        with top_row:
            show_rule_metrics(metrics)
            show_confusion_matrix(metrics)

        with bottom_row:
            left, right = st.columns([1.2, 1])
            with left:
                show_flagged_distribution(tx, y_pred)
            with right:
                show_risk_score_distribution(tx)

        st.markdown("---")
        show_sample_transactions(tx, y_pred, title_suffix=f"risk_score_rules ≥ {threshold:0.1f}")

    else:
        # Single rule view
        show_rule_summary_header(rule)

        if rule not in tx.columns:
            st.error(f"Column '{rule}' not found in transactions. Did you run the simulation script?")
            return

        y_pred = tx[rule].values
        y_true = tx["is_fraud"].values
        metrics = compute_metrics(y_pred, y_true)

        # show precomputed summary if available
        row_eval = eval_df[eval_df["rule"] == rule]
        if not row_eval.empty:
            st.caption(
                f"Precomputed evaluation – precision: {format_pct(row_eval['precision'].iloc[0])}, "
                f"recall: {format_pct(row_eval['recall'].iloc[0])}."
            )

        top_row = st.container()
        bottom_row = st.container()

        with top_row:
            show_rule_metrics(metrics)
            show_confusion_matrix(metrics)

        with bottom_row:
            left, right = st.columns([1.2, 1])
            with left:
                show_flagged_distribution(tx, y_pred)
            with right:
                show_risk_score_distribution(tx)

        st.markdown("---")
        show_sample_transactions(tx, y_pred, title_suffix=rule)


# -------------------------------------------------------------------
# ENTRYPOINT
# -------------------------------------------------------------------
if __name__ == "__main__":
    page_rule_console()

from __future__ import annotations
import pandas as pd
from pathlib import Path
from datetime import datetime
import json

from scorecard import (
    load_config,
    occupation_to_group,
    compute_tenure_days,
    enrich_watchlist,
    apply_scorecard,
)
from data_quality import run_data_quality

BASE = Path(__file__).resolve().parents[1]
DATA_DIR = BASE /"aml_suspicious_activity_monitoring" / "data"
KYC_DIR = BASE / "explainable_kyc_client_risk_scoring"
OUT_DIR = BASE / "explainable_kyc_client_risk_scoring" / "outputs"


def build_behavioral_features(
    clients: pd.DataFrame,
    tx: pd.DataFrame,
    country_risk: pd.DataFrame,
) -> pd.DataFrame:
    """
    Build 90/30/180 day behavioural features per client:
    - intl_rate_90d
    - hrc_hits_90d
    - swift_out_90d
    - cash_structuring_hits_30d
    - large_value_rate_180d
    - geo_diversity_180d
    """
    tx = tx.copy()
    tx["ts"] = pd.to_datetime(tx["ts"], errors="coerce")
    tx["dt"] = tx["ts"].dt.date

    # join residency to compute cross-border flag
    tx = tx.merge(
        clients[["client_id", "residency_country"]],
        on="client_id",
        how="left",
        suffixes=("", "_client"),
    )

    cr = country_risk[["country", "is_high_risk"]].rename(
        columns={"country": "cp_country"}
    )
    tx = tx.merge(
        cr,
        left_on="counterparty_country",
        right_on="cp_country",
        how="left",
    )

    tx["is_hrc"] = tx["is_high_risk"].fillna(0).astype(int)
    tx["is_swift_out"] = (
        (tx["channel"] == "swift") & (tx["direction"] == "out")
    ).astype(int)
    tx["is_structuring"] = (
        (tx["channel"] == "cash")
        & (tx["amount_usd"].between(8000, 9999))
    ).astype(int)
    tx["is_large"] = (tx["amount_usd"] >= 100000).astype(int)
    tx["is_intl"] = (
        tx["counterparty_country"] != tx["residency_country"]
    ).astype(int)

    # define "today" as max ts date
    as_of = tx["ts"].max().date()

    def window_mask(days: int):
        return tx["dt"] >= (as_of - pd.Timedelta(days=days))

    # 90d window
    tx_90 = tx[window_mask(90)].groupby("client_id")
    agg_90 = tx_90.agg(
        tx_90d=("ts", "count"),
        intl_rate_90d=("is_intl", "mean"),
        hrc_hits_90d=("is_hrc", "sum"),
        swift_out_90d=("is_swift_out", "sum"),
    )

    # 30d window
    tx_30 = tx[window_mask(30)].groupby("client_id")
    agg_30 = tx_30.agg(
        cash_structuring_hits_30d=("is_structuring", "sum"),
    )

    # 180d window
    tx_180 = tx[window_mask(180)].groupby("client_id")
    agg_180 = tx_180.agg(
        large_value_rate_180d=("is_large", "mean"),
        geo_diversity_180d=("counterparty_country", "nunique"),
    )

    beh = pd.DataFrame({"client_id": clients["client_id"].unique()})
    beh = beh.merge(agg_90, on="client_id", how="left")
    beh = beh.merge(agg_30, on="client_id", how="left")
    beh = beh.merge(agg_180, on="client_id", how="left")
    beh = beh.fillna(0)

    return beh


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    # Load core data
    clients = pd.read_csv(DATA_DIR / "clients.csv")
    tx = pd.read_csv(DATA_DIR / "transactions.csv")
    country_risk = pd.read_csv(DATA_DIR / "country_risk.csv")
    cfg = load_config(KYC_DIR / "config.yaml")
    watchlist = pd.read_csv(KYC_DIR / "watchlist.csv")

    # Data quality flags
    qc = run_data_quality(clients, country_risk)
    clients = clients.merge(
        qc.rename("qc_flags"),
        left_on="client_id",
        right_index=True,
        how="left",
    )

    # Static KYC features
    as_of_ts = pd.to_datetime(tx["ts"], errors="coerce").max()
    clients["occupation_group"] = clients["occupation"].apply(
        occupation_to_group
    )
    clients["tenure_days"] = compute_tenure_days(
        clients["onboard_date"], as_of_ts
    )

    # Residency risk
    cr_res = country_risk[["country", "risk_score", "is_high_risk"]].rename(
        columns={"country": "residency_country"}
    )
    clients = clients.merge(cr_res, on="residency_country", how="left")
    clients = clients.rename(
        columns={
            "risk_score": "residency_country_risk_score",
            "is_high_risk": "residency_country_is_high",
        }
    )

    # Behavioural features
    beh = build_behavioral_features(clients, tx, country_risk)

    # Merge everything
    feats = clients.merge(beh, on="client_id", how="left")

    # Watchlist enrichment
    feats = enrich_watchlist(feats, watchlist, cfg)

    # Apply scorecard
    scored = apply_scorecard(feats, cfg)

    # Output columns
    out_cols = [
        "client_id",
        "client_name",
        "residency_country",
        "pep_flag",
        "pep_match",
        "sanction_match",
        "residency_country_risk_score",
        "residency_country_is_high",
        "occupation",
        "occupation_group",
        "tenure_days",
        "intl_rate_90d",
        "hrc_hits_90d",
        "swift_out_90d",
        "cash_structuring_hits_30d",
        "large_value_rate_180d",
        "geo_diversity_180d",
        "risk_score",
        "risk_tier",
        "top_factors",
        "name_similarity",
        "qc_flags",
    ]
    scored_out = scored[out_cols].copy()
    scored_out["created_at"] = datetime.utcnow().isoformat(timespec="seconds")

    # Save client risk scores
    out_path = OUT_DIR / "client_risk_scores.csv"
    scored_out.to_csv(out_path, index=False)

    # Save manifest
    manifest = {
        "model": "kyc_risk_scorecard",
        "version": cfg.get("version"),
        "created_at_utc": datetime.utcnow().isoformat(timespec="seconds"),
        "n_clients": int(scored_out.shape[0]),
        "tier_counts": scored_out["risk_tier"].value_counts().to_dict(),
        "dq_summary": {
            "with_issues": int(
                (scored_out["qc_flags"].astype(str) != "").sum()
            )
        },
        "config_path": str(KYC_DIR / "config.yaml"),
    }
    with open(KYC_DIR / "run_manifest.json", "w") as f:
        json.dump(manifest, f, indent=2)

    print(f"Wrote {out_path}")
    print(f"Wrote {KYC_DIR / 'run_manifest.json'}")


if __name__ == "__main__":
    main()

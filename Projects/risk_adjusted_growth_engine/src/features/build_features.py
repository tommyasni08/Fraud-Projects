import argparse, os
import pandas as pd
import numpy as np
from pathlib import Path

# Directory of the current file
base_dir = Path(__file__).resolve().parents[2]

def add_rolls(df, group_key, cols, wins=(2,4)):
    df = df.sort_values([group_key, "week"]).copy()
    for w in wins:
        for c in cols:
            # lag 1
            df[f"{c}_lag1"] = df.groupby(group_key)[c].shift(1)
            # rolling mean/sum (excluding current week)
            df[f"{c}_rmean_{w}"] = (
                df.groupby(group_key)[c]
                  .shift(1)
                  .rolling(w, min_periods=1)
                  .mean()
            )
            df[f"{c}_rsum_{w}"] = (
                df.groupby(group_key)[c]
                  .shift(1)
                  .rolling(w, min_periods=1)
                  .sum()
            )
    return df

def one_hot_arm(df):
    arms = df["arm"].fillna("control").astype(str).values
    for a in ["control","education_nudge","personalized_reco","reco_small_bonus"]:
        df[f"arm__{a}"] = (arms == a).astype(int)
    return df

def build_features(raw_dir, out_dir, min_weeks):
    users = pd.read_csv(os.path.join(raw_dir, "users.csv"), parse_dates=["signup_date"])
    beh = pd.read_csv(os.path.join(raw_dir, "behavior_weekly.csv"), parse_dates=["week_start"])

    # Basic derived metrics
    beh["active_flag"] = ((beh["logins"] > 0) | (beh["num_trades"] > 0) | (beh["deposit_attempts"] > 0)).astype(int)
    beh["gmv_proxy"] = beh["num_trades"] * beh["avg_trade_size"].clip(lower=0)
    beh["loss_rate_gmv"] = np.where(beh["gmv_proxy"]>0, (beh["loss_fraud"]+beh["loss_bonus_abuse"]) / beh["gmv_proxy"], 0.0)

    # Rolling/lag features
    roll_cols = ["logins","sessions","education_clicks","num_trades","avg_trade_size",
                 "portfolio_value","deposit_attempts","deposit_success_amt","withdrawal_amt",
                 "revenue_gross","net_revenue","loss_fraud","loss_bonus_abuse","gmv_proxy","active_flag"]
    beh = add_rolls(beh, "user_id", roll_cols, wins=(2,4))

    # One-hot arms
    beh = one_hot_arm(beh)

    # Targets ensure int
    for t in ["dep_increase_7d","fraud_flag_14d","abuse_flag_14d"]:
        if t in beh.columns:
            beh[t] = beh[t].astype(int)

    # Join static user features
    feat = beh.merge(users, on="user_id", how="left")

    # Cold-start filter
    feat = feat[feat["week"] >= min_weeks].reset_index(drop=True)

    keep = [
        "user_id","week","week_start","account_age_days","country","channel_src","device_type","kyc_score","risk_tier",
        "arm","bonus_cost",
        "active_flag","gmv_proxy","loss_rate_gmv",
        "logins","sessions","education_clicks","num_trades","avg_trade_size","portfolio_value",
        "deposit_attempts","deposit_success_amt","withdrawal_amt",
        "revenue_gross","loss_fraud","loss_bonus_abuse","net_revenue",
        "dep_increase_7d","fraud_flag_14d","abuse_flag_14d",
        "arm__control","arm__education_nudge","arm__personalized_reco","arm__reco_small_bonus",
    ]
    engineered = [c for c in feat.columns if any(s in c for s in ["_lag1","_rmean_","_rsum_"])]
    keep_extended = [c for c in keep if c in feat.columns] + engineered
    feat_curated = feat[keep_extended].copy()

    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "features_user_week.csv")
    feat_curated.to_csv(out_path, index=False)

    meta = {
        "rows": int(len(feat_curated)),
        "cols": int(len(feat_curated.columns)),
        "targets": ["dep_increase_7d","fraud_flag_14d","abuse_flag_14d"],
        "treatment_col": "arm",
        "one_hot_treatments": ["arm__control","arm__education_nudge","arm__personalized_reco","arm__reco_small_bonus"],
        "primary_kpi": "net_revenue",
        "guardrails": ["loss_rate_gmv","loss_fraud","loss_bonus_abuse"]
    }
    with open(os.path.join(out_dir, "features_meta.json"), "w") as f:
        import json; json.dump(meta, f, indent=2)

    print(f"Wrote {out_path} with shape {feat_curated.shape}")
    print(f"Wrote {os.path.join(out_dir, 'features_meta.json')}")

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--raw", type=str, required=True)
    ap.add_argument("--out", type=str, required=True)
    ap.add_argument("--min_weeks", type=int, default=2)
    args = ap.parse_args()

    raw_path = base_dir / args.raw
    out_path = base_dir / args.out

    build_features(raw_path, out_path, args.min_weeks)

if __name__ == "__main__":
    main()

    #   "args": [
    #     "--raw",
    #     "data/raw",
    #     "--out",
    #     "data/processed",
    #     "--min_weeks",
    #     "2"
    #   ]
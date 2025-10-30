#!/usr/bin/env python
import argparse, os, numpy as np, pandas as pd, yaml
from datetime import datetime, timedelta
from pathlib import Path
rng = np.random.default_rng(42)

# Directory of the current file
base_dir = Path(__file__).resolve().parents[2]

# Construct a safe path (recommended instead of raw "../../../")
config_path = base_dir / "configs" / "sim.yaml"

# Load YAML file
with open(config_path, "r") as f:
    config = yaml.safe_load(f)

# Assign constants (uppercase for readability)
COUNTRIES = config["countries"]
CHANNELS = config["channels"]
DEVICES  = config["devices"]

def simulate_users(n_users:int, seed:int=42):
    rng = np.random.default_rng(seed)
    user_id = np.arange(1, n_users+1)
    signup_offsets = rng.integers(0, 60, size=n_users)
    signup_date = pd.to_datetime(config['start_date']) + pd.to_timedelta(signup_offsets, unit="D")
    country = rng.choice(COUNTRIES, size=n_users, p=[0.35,0.25,0.15,0.15,0.10])
    channel = rng.choice(CHANNELS, size=n_users, p=[0.30,0.40,0.15,0.15])
    device = rng.choice(DEVICES, size=n_users, p=[0.35,0.50,0.15])
    kyc_score = np.clip(rng.normal(0.75, 0.15, n_users), 0, 1)
    # Derive risk tiers: lower kyc_score => higher risk
    # Sample risk tier by kyc band with different probabilities
    risk_tier = np.empty(n_users, dtype=object)
    band1 = kyc_score > 0.8
    band2 = (kyc_score > 0.6) & (kyc_score <= 0.8)
    band3 = kyc_score <= 0.6
    if band1.any():
        risk_tier[band1] = rng.choice(["low","medium","high"], size=band1.sum(), p=[0.8,0.18,0.02])
    if band2.any():
        risk_tier[band2] = rng.choice(["low","medium","high"], size=band2.sum(), p=[0.5,0.4,0.1])
    if band3.any():
        risk_tier[band3] = rng.choice(["low","medium","high"], size=band3.sum(), p=[0.2,0.5,0.3])
    # Device hash overlaps: small chance some devices are shared by multiple users
    base_device_hash = rng.integers(1_000_000, 9_999_999, size=n_users)
    shared_mask = rng.random(n_users) < 0.05
    # For shared devices, force some repeats by sampling from existing hashes
    if shared_mask.sum() > 0:
        base_device_hash[shared_mask] = rng.choice(base_device_hash[~shared_mask], size=shared_mask.sum())
    df = pd.DataFrame({
        "user_id": user_id,
        "signup_date": signup_date,
        "country": country,
        "channel_src": channel,
        "device_type": device,
        "device_id_hash": base_device_hash,
        "kyc_score": kyc_score.round(3),
        "risk_tier": risk_tier
    })
    return df

def simulate_weeks(users:pd.DataFrame, n_weeks:int, seed:int=42):
    rng = np.random.default_rng(seed+1)
    rows = []
    for w in range(n_weeks):
        week_start = pd.to_datetime(config['start_date']) + pd.DateOffset(months=1) + pd.to_timedelta(7*w, unit="D")
        account_age = (week_start - users["signup_date"]).dt.days.clip(lower=0)
        # Engagement scales with account_age (rise then plateau) and country/device
        base_eng = np.log1p(account_age) + rng.normal(0, 0.3, size=len(users))
        country_adj = users["country"].map({"SG":0.3,"ID":0.0,"MY":0.05,"PH":-0.05,"VN":0.1}).values
        device_adj = users["device_type"].map({"ios":0.1,"android":0.05,"web":-0.05}).values
        engagement = np.clip(base_eng + country_adj + device_adj, 0, None)
        logins = np.clip((engagement*3 + rng.normal(0,1,len(users))).round().astype(int), 0, None)
        sessions = np.clip((engagement*2 + rng.normal(0,1,len(users))).round().astype(int), 0, None)
        watchlist = np.clip((engagement*1.5 + rng.normal(0,1,len(users))).round().astype(int), 0, None)
        edu_clicks = np.clip((engagement*0.8 + rng.normal(0,1,len(users))).round().astype(int), 0, None)

        # Trading behavior
        num_trades = np.clip((engagement*0.7 + rng.normal(0,0.8,len(users))).round().astype(int), 0, None)
        avg_trade_size = np.clip(rng.normal(200, 75, len(users)) * (1 + engagement*0.1), 20, None)
        portfolio_value = np.clip(rng.normal(1500, 600, len(users)) * (1 + engagement*0.2), 0, None)
        realized_pnl = rng.normal(0, 15, len(users)) * np.sqrt(np.maximum(num_trades,1))

        # Payments
        deposit_attempts = np.clip((engagement*0.4 + rng.normal(0,0.6,len(users))).round().astype(int), 0, None)
        deposit_success_amt = np.clip(deposit_attempts * rng.normal(60, 30, len(users)) * (1+engagement*0.05), 0, None)
        withdrawal_amt = np.clip((rng.normal(30, 25, len(users)) * (1 + (rng.random(len(users))<0.1))).round(), 0, None)

        # Fraud & abuse signals
        shared_device_users = pd.Series(users["device_id_hash"]).map(pd.Series(users["device_id_hash"]).value_counts()).values
        velocity_deposits_24h = (deposit_attempts > 3).astype(int)
        impossible_travel_flag = (rng.random(len(users)) < 0.005).astype(int)
        kyc_mismatch_flag = (users["kyc_score"].values < 0.45).astype(int)
        bonus_redeem_cnt = (rng.random(len(users)) < 0.15).astype(int) * rng.integers(0,2,len(users))

        # Treatments / arms (randomized here; later we learn a policy)
        arms = np.array(["control","education_nudge","personalized_reco","reco_small_bonus"])
        arm = rng.choice(arms, size=len(users), p=[0.4,0.25,0.25,0.10])
        bonus_cost = np.where(arm=="reco_small_bonus", 0.5, 0.0)

        # Revenue model (illustrative)
        trade_revenue = num_trades * (avg_trade_size * 0.0008)  # ~8 bps fee proxy
        spread_revenue = np.clip(num_trades,0,None) * 0.02
        revenue_gross = trade_revenue + spread_revenue

        # Losses: fraud & bonus abuse (stochastic, higher with certain signals)
        fraud_prob = (0.01
                      + 0.015*(shared_device_users>1)
                      + 0.02*velocity_deposits_24h
                      + 0.015*kyc_mismatch_flag
                      + 0.005*(arm=="reco_small_bonus"))
        fraud_flag = (rng.random(len(users)) < np.clip(fraud_prob, 0, 0.5)).astype(int)
        loss_fraud = fraud_flag * rng.normal(40, 25, len(users)).clip(5, 300)

        abuse_prob = (0.01 + 0.02*(arm=="reco_small_bonus") + 0.005*(bonus_redeem_cnt>0))
        abuse_flag = (rng.random(len(users)) < np.clip(abuse_prob, 0, 0.6)).astype(int)
        loss_bonus_abuse = abuse_flag * rng.normal(0.5, 0.3, len(users)).clip(0, 3)

        net_revenue = revenue_gross - loss_fraud - loss_bonus_abuse - bonus_cost

        rows.append(pd.DataFrame({
            "user_id": users["user_id"].values,
            "week": w,
            "week_start": week_start,
            "account_age_days": account_age,
            "logins": logins,
            "sessions": sessions,
            "watchlist_events": watchlist,
            "education_clicks": edu_clicks,
            "num_trades": num_trades,
            "avg_trade_size": avg_trade_size.round(2),
            "portfolio_value": portfolio_value.round(2),
            "realized_pnl": realized_pnl.round(2),
            "deposit_attempts": deposit_attempts,
            "deposit_success_amt": deposit_success_amt.round(2),
            "withdrawal_amt": withdrawal_amt,
            "shared_device_users": shared_device_users,
            "velocity_deposits_24h": velocity_deposits_24h,
            "impossible_travel_flag": impossible_travel_flag,
            "kyc_mismatch_flag": kyc_mismatch_flag,
            "bonus_redeem_cnt": bonus_redeem_cnt,
            "arm": arm,
            "bonus_cost": bonus_cost,
            "revenue_gross": revenue_gross.round(3),
            "loss_fraud": loss_fraud.round(3),
            "loss_bonus_abuse": loss_bonus_abuse.round(3),
            "net_revenue": net_revenue.round(3)
        }))
    return pd.concat(rows, ignore_index=True)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--output", type=str, required=True)
    ap.add_argument("--users", type=int, default=10000)
    ap.add_argument("--weeks", type=int, default=12)
    ap.add_argument("--seed", type=int, default=42)
    args = ap.parse_args()

    output_path = base_dir / args.output

    os.makedirs(args.output, exist_ok=True)
    users = simulate_users(args.users, seed=args.seed)
    weeks = simulate_weeks(users, n_weeks=args.weeks, seed=args.seed)

    # Derive label-style outcomes (for modeling later)
    # Example: deposit increase vs prior week and fraud/abuse targets
    weeks_sorted = weeks.sort_values(["user_id","week"]).copy()
    weeks_sorted["deposit_prev"] = weeks_sorted.groupby("user_id")["deposit_success_amt"].shift(1).fillna(0)
    weeks_sorted["dep_increase_7d"] = (weeks_sorted["deposit_success_amt"] > weeks_sorted["deposit_prev"]).astype(int)

    # Fraud/abuse flags already in frame; create 14d targets by OR over last two weeks (approx for demo)
    weeks_sorted["fraud_flag_14d"] = weeks_sorted.groupby("user_id")["loss_fraud"].apply(lambda s: (s>0).rolling(2, min_periods=1).max()).reset_index(level=0, drop=True).astype(int)
    weeks_sorted["abuse_flag_14d"] = weeks_sorted.groupby("user_id")["loss_bonus_abuse"].apply(lambda s: (s>0).rolling(2, min_periods=1).max()).reset_index(level=0, drop=True).astype(int)

    # Save CSVs
    users.to_csv(os.path.join(output_path, "users.csv"), index=False)
    weeks_sorted.to_csv(os.path.join(output_path, "behavior_weekly.csv"), index=False)

    print(f"Wrote users.csv ({len(users)}) and behavior_weekly.csv ({len(weeks_sorted)}) to {args.output}")

if __name__ == "__main__":
    main()

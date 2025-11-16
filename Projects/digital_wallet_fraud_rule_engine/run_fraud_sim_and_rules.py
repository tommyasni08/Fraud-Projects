import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from pathlib import Path


RNG = np.random.default_rng(123)

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(exist_ok=True)

TXN_PATH = DATA_DIR / "transactions_with_scenarios.csv"
EVAL_PATH = DATA_DIR / "rule_evaluation_summary.csv"


# -------------------------------------------------------------------
# 1) Synthetic digital wallet + fraud scenarios
# -------------------------------------------------------------------

def random_ts(start: datetime, end: datetime, size: int):
    start_u = start.timestamp()
    end_u = end.timestamp()
    return pd.to_datetime(RNG.uniform(start_u, end_u, size), unit="s")


def generate_base_users(n_users=4000, start_date=datetime(2025, 1, 1), n_days=60):
    signup_dates = RNG.integers(0, n_days, size=n_users)
    signup_dates = [start_date + timedelta(days=int(d)) for d in signup_dates]
    countries = RNG.choice(["SG", "ID", "MY", "PH", "TH", "VN"], size=n_users,
                           p=[0.3, 0.25, 0.15, 0.1, 0.1, 0.1])
    risk_segment = RNG.choice(["low", "medium", "high"], size=n_users,
                              p=[0.6, 0.3, 0.1])

    users = pd.DataFrame({
        "user_id": np.arange(1, n_users + 1),
        "signup_ts": signup_dates,
        "country": countries,
        "risk_segment": risk_segment,
    })
    return users


def generate_base_devices(users, n_devices=3000):
    device_ids = np.arange(1, n_devices + 1)
    # each user 1–2 devices
    n_dev_per_user = RNG.choice([1, 2], size=len(users), p=[0.8, 0.2])

    rows = []
    for idx, row in users.iterrows():
        uid = row["user_id"]
        k = n_dev_per_user[idx]
        chosen = RNG.choice(device_ids, size=k, replace=False)
        for d in chosen:
            rows.append({"user_id": uid, "device_id": int(d)})

    mapping = pd.DataFrame(rows)

    # device risk features
    devices = pd.DataFrame({
        "device_id": device_ids,
        "is_emulator": RNG.choice([0, 1], size=n_devices, p=[0.97, 0.03]),
        "is_rooted": RNG.choice([0, 1], size=n_devices, p=[0.94, 0.06]),
    })
    devices["device_risk_score"] = (
        devices["is_emulator"] * RNG.uniform(0.4, 0.8, size=n_devices) +
        devices["is_rooted"] * RNG.uniform(0.4, 0.7, size=n_devices) +
        RNG.uniform(0, 0.3, size=n_devices)
    ).round(3)

    return users, devices, mapping


def simulate_normal_transactions(users, mapping, start_date, n_days, n_txn=80_000):
    """
    Generate mostly normal behavior: topups, p2p, merchant payments, withdrawals.
    Fraud will be overlaid later.
    """
    end_date = start_date + timedelta(days=n_days)

    user_ids = users["user_id"].values
    signup_ts = pd.to_datetime(users["signup_ts"]).values

    # activity weight: high-risk segments slightly more active
    base_activity = RNG.gamma(2.0, 1.0, size=len(users))
    risk_mult = users["risk_segment"].map({"low": 0.8, "medium": 1.0, "high": 1.2}).values
    weights = base_activity * risk_mult
    weights = weights / weights.sum()

    chosen_users = RNG.choice(user_ids, size=n_txn, p=weights)
    tx_ts = random_ts(start_date, end_date, size=n_txn)
    tx_type = RNG.choice(
        ["topup", "p2p_transfer", "merchant_payment", "withdrawal"],
        size=n_txn,
        p=[0.35, 0.25, 0.3, 0.1],
    )

    # base amounts
    amounts = []
    for t in tx_type:
        if t == "topup":
            amt = RNG.gamma(2.0, 60)   # ~120
        elif t == "p2p_transfer":
            amt = RNG.gamma(1.5, 40)   # ~60
        elif t == "merchant_payment":
            amt = RNG.gamma(2.0, 50)   # ~100
        else:  # withdrawal
            amt = RNG.gamma(2.0, 80)   # ~160
        amounts.append(float(np.clip(amt, 1, 4000)))
    amounts = np.array(amounts).round(2)

    # status mostly success
    status = RNG.choice(
        ["success", "failed"],
        size=n_txn,
        p=[0.94, 0.06],
    )

    # sample device per user
    user_dev = mapping.groupby("user_id")["device_id"].apply(list).to_dict()
    device_ids = []
    for u in chosen_users:
        devs = user_dev.get(u, [])
        if devs:
            device_ids.append(int(RNG.choice(devs)))
        else:
            device_ids.append(np.nan)

    users_idx = users.set_index("user_id")
    countries = users_idx.loc[chosen_users, "country"].values
    risk_segment = users_idx.loc[chosen_users, "risk_segment"].values

    # initial "normal" fraud label = 0, scenario = normal
    tx = pd.DataFrame({
        "txn_id": np.arange(1, n_txn + 1),
        "user_id": chosen_users,
        "device_id": device_ids,
        "txn_ts": tx_ts,
        "txn_date": pd.to_datetime(tx_ts).date,
        "txn_type": tx_type,
        "amount": amounts,
        "status": status,
        "country": countries,
        "risk_segment": risk_segment,
        "fraud_scenario": "normal",
        "is_fraud": 0,
    })

    # ensure no tx before signup
    users_signup = users.set_index("user_id")["signup_ts"]
    tx["signup_ts"] = tx["user_id"].map(users_signup)
    tx["signup_ts"] = pd.to_datetime(tx["signup_ts"])
    tx = tx[tx["txn_ts"] >= tx["signup_ts"]].copy()
    tx.drop(columns=["signup_ts"], inplace=True)
    tx.reset_index(drop=True, inplace=True)
    tx["txn_id"] = np.arange(1, len(tx) + 1)

    return tx


# -------------------------------------------------------------------
# 2) Overlay fraud scenarios
# -------------------------------------------------------------------

def inject_velocity_attacks(tx, n_attacks=150):
    """
    For chosen users, create short bursts of many outgoing transactions.
    """
    tx = tx.copy()
    victim_users = RNG.choice(tx["user_id"].unique(), size=n_attacks, replace=False)

    attack_rows = []
    attack_id_base = tx["txn_id"].max() + 1
    attack_count = 0

    for u in victim_users:
        # choose a random time window
        user_tx = tx[tx["user_id"] == u]
        if user_tx.empty:
            continue
        base_time = user_tx["txn_ts"].sample(1, random_state=int(RNG.integers(0, 1e6))).iloc[0]
        for _ in range(RNG.integers(5, 20)):  # many small tx
            ts = base_time + timedelta(minutes=int(RNG.integers(0, 20)))
            amt = float(np.clip(RNG.gamma(1.0, 50), 5, 800))  # small-mid sized
            attack_rows.append({
                "txn_id": attack_id_base + attack_count,
                "user_id": u,
                "device_id": tx.loc[user_tx.index[0], "device_id"],
                "txn_ts": ts,
                "txn_date": ts.date(),
                "txn_type": RNG.choice(["p2p_transfer", "merchant_payment"]),
                "amount": amt,
                "status": "success",
                "country": tx.loc[user_tx.index[0], "country"],
                "risk_segment": tx.loc[user_tx.index[0], "risk_segment"],
                "fraud_scenario": "velocity_attack",
                "is_fraud": 1,
            })
            attack_count += 1

    if attack_rows:
        tx_attack = pd.DataFrame(attack_rows)
        tx = pd.concat([tx, tx_attack], ignore_index=True)
        tx = tx.sort_values("txn_ts").reset_index(drop=True)
        tx["txn_id"] = np.arange(1, len(tx) + 1)

    return tx


def inject_cashout_after_topup(tx, n_patterns=200):
    """
    Identify large topups and create immediate withdrawals / p2p transfers.
    """
    tx = tx.copy()
    # choose candidate high-value topups
    candidates = tx[(tx["txn_type"] == "topup") & (tx["amount"] > 800)].copy()
    if candidates.empty:
        return tx

    chosen = candidates.sample(min(n_patterns, len(candidates)), random_state=42)
    new_rows = []
    new_id_base = tx["txn_id"].max() + 1
    count = 0

    for _, row in chosen.iterrows():
        u = row["user_id"]
        base_time = row["txn_ts"]
        # simulate 1–3 cashout moves
        num_moves = int(RNG.integers(1, 4))
        remaining = row["amount"]
        for _ in range(num_moves):
            frac = RNG.uniform(0.3, 0.7)
            amt = float(np.clip(remaining * frac, 10, remaining))
            remaining -= amt
            ts = base_time + timedelta(minutes=int(RNG.integers(5, 60)))
            new_rows.append({
                "txn_id": new_id_base + count,
                "user_id": u,
                "device_id": row["device_id"],
                "txn_ts": ts,
                "txn_date": ts.date(),
                "txn_type": RNG.choice(["p2p_transfer", "withdrawal"]),
                "amount": amt,
                "status": "success",
                "country": row["country"],
                "risk_segment": row["risk_segment"],
                "fraud_scenario": "cashout_after_topup",
                "is_fraud": 1,
            })
            count += 1

    if new_rows:
        tx_new = pd.DataFrame(new_rows)
        tx = pd.concat([tx, tx_new], ignore_index=True)
        tx = tx.sort_values("txn_ts").reset_index(drop=True)
        tx["txn_id"] = np.arange(1, len(tx) + 1)

    return tx


def inject_device_farming(tx, device_mapping, n_devices=80):
    """
    Choose devices shared by many users and mark part of their activity as fraud.
    """
    tx = tx.copy()

    user_per_device = device_mapping.groupby("device_id")["user_id"].nunique()
    shared_devices = user_per_device[user_per_device >= 3].index.tolist()
    if not shared_devices:
        return tx

    chosen_devices = RNG.choice(shared_devices, size=min(n_devices, len(shared_devices)), replace=False)

    mask = tx["device_id"].isin(chosen_devices)
    candidate_tx = tx[mask].copy()

    if candidate_tx.empty:
        return tx

    # randomly pick a subset to mark as fraud
    idx = candidate_tx.sample(frac=0.4, random_state=123).index
    tx.loc[idx, "fraud_scenario"] = "device_farming"
    tx.loc[idx, "is_fraud"] = 1

    return tx


def inject_new_account_abuse(tx, users, n_users_abuse=200):
    """
    New users with high spending within first 24h of signup.
    """
    tx = tx.copy()
    users = users.copy()

    users["signup_ts"] = pd.to_datetime(users["signup_ts"])
    chosen_users = users.sample(min(n_users_abuse, len(users)), random_state=99)["user_id"].values

    # for each chosen user, mark some early high spend as fraud
    tx["txn_ts"] = pd.to_datetime(tx["txn_ts"])
    users_signup = users.set_index("user_id")["signup_ts"]

    for u in chosen_users:
        signup = users_signup.loc[u]
        early_window = signup + timedelta(hours=24)
        user_early_tx = tx[
            (tx["user_id"] == u) &
            (tx["txn_ts"] >= signup) &
            (tx["txn_ts"] <= early_window) &
            (tx["amount"] > 200)
        ]
        if user_early_tx.empty:
            continue
        idx = user_early_tx.sample(frac=0.5, random_state=int(RNG.integers(0, 1e6))).index
        tx.loc[idx, "fraud_scenario"] = "new_account_abuse"
        tx.loc[idx, "is_fraud"] = 1

    return tx


def inject_geo_anomaly(tx, n_events=300):
    """
    Randomly label some large high-risk-country transactions as fraud.
    """
    tx = tx.copy()
    high_risk_countries = ["ID", "PH", "VN"]
    mask = (tx["country"].isin(high_risk_countries)) & (tx["amount"] > 500)
    candidates = tx[mask]
    if candidates.empty:
        return tx

    chosen = candidates.sample(min(n_events, len(candidates)), random_state=321).index
    tx.loc[chosen, "fraud_scenario"] = "geo_anomaly"
    tx.loc[chosen, "is_fraud"] = 1

    return tx


def generate_fraud_dataset():
    start_date = datetime(2025, 1, 1)
    n_days = 90

    print("Generating users and devices...")
    users = generate_base_users(n_users=4000, start_date=start_date, n_days=n_days)
    users, devices, mapping = generate_base_devices(users, n_devices=3000)

    print("Simulating baseline transactions...")
    tx = simulate_normal_transactions(users, mapping, start_date, n_days, n_txn=80_000)

    print("Injecting fraud scenarios...")
    tx = inject_velocity_attacks(tx)
    tx = inject_cashout_after_topup(tx)
    tx = inject_device_farming(tx, mapping)
    tx = inject_new_account_abuse(tx, users)
    tx = inject_geo_anomaly(tx)

    # final ordering
    tx = tx.sort_values("txn_ts").reset_index(drop=True)
    tx["txn_id"] = np.arange(1, len(tx) + 1)

    tx.to_csv(TXN_PATH, index=False)
    print(f"Saved transactions with fraud scenarios to {TXN_PATH}")

    # return also mapping for later use
    return tx, users, devices, mapping


# -------------------------------------------------------------------
# 3) Rule engine
# -------------------------------------------------------------------

def build_derived_features(tx, users, mapping):
    tx = tx.copy()
    tx["txn_ts"] = pd.to_datetime(tx["txn_ts"])
    tx = tx.sort_values(["user_id", "txn_ts"])

    # time since signup
    users_signup = users.set_index("user_id")["signup_ts"]
    users_signup = pd.to_datetime(users_signup)
    tx["signup_ts"] = tx["user_id"].map(users_signup)
    tx["time_since_signup_hours"] = (tx["txn_ts"] - tx["signup_ts"]).dt.total_seconds() / 3600

    # user-level rolling velocity features (coarse: same-day approximation)
    tx["txn_date"] = tx["txn_ts"].dt.date
    # group by user & date for counts/sums
    agg_daily = tx.groupby(["user_id", "txn_date"]).agg(
        daily_txn_count=("txn_id", "count"),
        daily_txn_amount=("amount", "sum"),
    ).reset_index()
    tx = tx.merge(agg_daily, on=["user_id", "txn_date"], how="left")

    # device-level user count
    dev_users = mapping.groupby("device_id")["user_id"].nunique().rename("device_user_count").reset_index()
    tx = tx.merge(dev_users, on="device_id", how="left")
    tx["device_user_count"].fillna(1, inplace=True)

    # country risk flag
    tx["is_high_risk_country"] = tx["country"].isin(["ID", "PH", "VN"]).astype(int)
    tx["is_high_risk_segment"] = (tx["risk_segment"] == "high").astype(int)

    return tx


def apply_rules(tx):
    tx = tx.copy()

    # R1: velocity – many tx and high amount in a day
    tx["R1_velocity"] = (
        (tx["daily_txn_count"] >= 8) &
        (tx["daily_txn_amount"] >= 1500)
    ).astype(int)

    # R2: cashout after topup – withdrawal/p2p with high daily amount
    tx["R2_cashout"] = (
        (tx["txn_type"].isin(["withdrawal", "p2p_transfer"])) &
        (tx["daily_txn_amount"] >= 2000)
    ).astype(int)

    # R3: device farming – device shared across many users with decent amount
    tx["R3_device_farming"] = (
        (tx["device_user_count"] >= 3) &
        (tx["amount"] >= 200)
    ).astype(int)

    # R4: new account high spend within 24h
    tx["R4_new_account_abuse"] = (
        (tx["time_since_signup_hours"] >= 0) &
        (tx["time_since_signup_hours"] <= 24) &
        (tx["amount"] >= 250)
    ).astype(int)

    # R5: geo anomaly – high amount from high-risk country
    tx["R5_geo_anomaly"] = (
        (tx["is_high_risk_country"] == 1) &
        (tx["amount"] >= 600)
    ).astype(int)

    # risk score = weighted sum
    weights = {
        "R1_velocity": 1.5,
        "R2_cashout": 1.8,
        "R3_device_farming": 1.2,
        "R4_new_account_abuse": 1.6,
        "R5_geo_anomaly": 1.0,
    }
    score = np.zeros(len(tx))
    for r, w in weights.items():
        score += tx[r].values * w
    tx["risk_score_rules"] = score

    # flag as suspicious if risk_score >= threshold
    tx["is_flagged_by_rules"] = (tx["risk_score_rules"] >= 1.5).astype(int)

    return tx


# -------------------------------------------------------------------
# 4) Evaluation
# -------------------------------------------------------------------

def evaluate_rules(tx):
    results = []

    for rule_col in ["R1_velocity", "R2_cashout", "R3_device_farming",
                     "R4_new_account_abuse", "R5_geo_anomaly"]:
        y_pred = tx[rule_col].values
        y_true = tx["is_fraud"].values

        tp = int(((y_pred == 1) & (y_true == 1)).sum())
        fp = int(((y_pred == 1) & (y_true == 0)).sum())
        fn = int(((y_pred == 0) & (y_true == 1)).sum())
        tn = int(((y_pred == 0) & (y_true == 0)).sum())

        precision = tp / (tp + fp) if (tp + fp) > 0 else np.nan
        recall = tp / (tp + fn) if (tp + fn) > 0 else np.nan

        results.append({
            "rule": rule_col,
            "tp": tp,
            "fp": fp,
            "fn": fn,
            "tn": tn,
            "precision": precision,
            "recall": recall,
        })

    # overall ruleset (is_flagged_by_rules)
    y_pred_all = tx["is_flagged_by_rules"].values
    y_true = tx["is_fraud"].values
    tp = int(((y_pred_all == 1) & (y_true == 1)).sum())
    fp = int(((y_pred_all == 1) & (y_true == 0)).sum())
    fn = int(((y_pred_all == 0) & (y_true == 1)).sum())
    tn = int(((y_pred_all == 0) & (y_true == 0)).sum())
    precision = tp / (tp + fp) if (tp + fp) > 0 else np.nan
    recall = tp / (tp + fn) if (tp + fn) > 0 else np.nan

    results.append({
        "rule": "ALL_RULES_COMBINED",
        "tp": tp,
        "fp": fp,
        "fn": fn,
        "tn": tn,
        "precision": precision,
        "recall": recall,
    })

    eval_df = pd.DataFrame(results)
    eval_df.to_csv(EVAL_PATH, index=False)
    print(f"Saved rule evaluation summary to {EVAL_PATH}")

    return eval_df


# -------------------------------------------------------------------
# MAIN
# -------------------------------------------------------------------

def main():
    print("=== Digital Wallet Fraud Simulation & Rule Engine ===")
    tx, users, devices, mapping = generate_fraud_dataset()
    print(f"Total transactions after fraud injection: {len(tx):,}")

    print("Building derived features for rules...")
    tx_feat = build_derived_features(tx, users, mapping)

    print("Applying rules...")
    tx_rules = apply_rules(tx_feat)

    print("Evaluating rules vs fraud labels...")
    eval_df = evaluate_rules(tx_rules)

    # Save enriched transactions as well
    tx_rules.to_csv(TXN_PATH, index=False)
    print(f"Saved enriched transactions with rule flags to {TXN_PATH}")

    print("\nRule evaluation summary:")
    print(eval_df)


if __name__ == "__main__":
    main()

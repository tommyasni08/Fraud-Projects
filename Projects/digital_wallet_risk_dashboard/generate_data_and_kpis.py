import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from pathlib import Path

# global RNG for reproducibility
RNG = np.random.default_rng(42)

# directories
BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
RAW_DIR = DATA_DIR / "raw"
PROCESSED_DIR = DATA_DIR / "processed"

for d in (RAW_DIR, PROCESSED_DIR):
    d.mkdir(parents=True, exist_ok=True)

# timeline
START_DATE = datetime(2025, 1, 1)
N_DAYS = 90
DATE_RANGE = [START_DATE + timedelta(days=i) for i in range(N_DAYS)]

# simple global constants
COUNTRIES = ["SG", "ID", "MY", "PH", "TH", "VN"]
CHANNELS = ["organic", "campaign", "referral"]
DEVICE_TYPES = ["android", "ios", "web"]
TXN_TYPES = ["topup", "p2p_transfer", "merchant_payment", "withdrawal", "refund"]


def random_dates(n, start, end):
    """Sample n random timestamps between start and end."""
    start_u = start.timestamp()
    end_u = end.timestamp()
    return pd.to_datetime(RNG.uniform(start_u, end_u, n), unit="s")


# -------------------------------------------------------------------
# 1) USERS
# -------------------------------------------------------------------
def generate_users(n_users=5000):
    signup_dates = RNG.choice(DATE_RANGE, size=n_users)
    countries = RNG.choice(COUNTRIES, size=n_users,
                           p=[0.3, 0.25, 0.15, 0.1, 0.1, 0.1])
    channels = RNG.choice(CHANNELS, size=n_users,
                          p=[0.6, 0.25, 0.15])
    risk_segment = RNG.choice(["low", "medium", "high"], size=n_users,
                              p=[0.6, 0.3, 0.1])
    kyc_status = RNG.choice(["unverified", "pending", "verified"], size=n_users,
                            p=[0.2, 0.1, 0.7])

    users = pd.DataFrame({
        "user_id": np.arange(1, n_users + 1),
        "signup_date": signup_dates,
        "country": countries,
        "channel": channels,
        "risk_segment": risk_segment,
        "kyc_status": kyc_status,
    }).sort_values("user_id")

    users.to_csv(RAW_DIR / "users.csv", index=False)
    return users


# -------------------------------------------------------------------
# 2) DEVICES + USER–DEVICE MAPPING
# -------------------------------------------------------------------
def generate_devices(n_devices=4000):
    devices = pd.DataFrame({
        "device_id": np.arange(1, n_devices + 1),
        "device_type": RNG.choice(DEVICE_TYPES, size=n_devices,
                                  p=[0.6, 0.35, 0.05]),
        "os_version": RNG.choice(["old", "mid", "new"], size=n_devices,
                                 p=[0.2, 0.5, 0.3]),
        "is_rooted_or_jailbroken": RNG.choice([0, 1], size=n_devices,
                                              p=[0.95, 0.05]),
        "is_emulator": RNG.choice([0, 1], size=n_devices,
                                  p=[0.97, 0.03]),
    })

    risk_scores = (
        devices["is_rooted_or_jailbroken"] * RNG.uniform(0.4, 0.8, size=len(devices))
        + devices["is_emulator"] * RNG.uniform(0.3, 0.7, size=len(devices))
        + RNG.uniform(0, 0.3, size=len(devices))
    )
    devices["risk_score_device"] = risk_scores.round(3)

    devices.to_csv(RAW_DIR / "devices.csv", index=False)
    return devices


def generate_user_device_mapping(users, devices):
    n_users = len(users)
    device_ids = devices["device_id"].values

    # each user has 1–3 devices, biased toward 1
    num_devices_per_user = RNG.choice([1, 2, 3], size=n_users,
                                      p=[0.7, 0.2, 0.1])
    rows = []

    for _, user in users.iterrows():
        uid = int(user["user_id"])
        k = num_devices_per_user[uid - 1]
        assigned = RNG.choice(device_ids, size=k, replace=False)
        first_seen = user["signup_date"]
        for d_id in assigned:
            last_seen = first_seen + timedelta(days=int(RNG.integers(0, N_DAYS)))
            rows.append({
                "user_id": uid,
                "device_id": int(d_id),
                "first_seen_ts": first_seen,
                "last_seen_ts": last_seen,
                "num_sessions": int(RNG.integers(3, 50)),
            })

    mapping = pd.DataFrame(rows)
    mapping.to_csv(RAW_DIR / "user_device_mapping.csv", index=False)
    return mapping


# -------------------------------------------------------------------
# 3) TRANSACTIONS
# -------------------------------------------------------------------
def generate_transactions(users, mapping, n_txn=120_000):
    # activity weight per user based on risk + randomness
    base_activity = RNG.gamma(shape=2.0, scale=1.0, size=len(users))
    risk_multiplier = users["risk_segment"].map(
        {"low": 0.8, "medium": 1.0, "high": 1.2}
    ).values
    activity_weight = base_activity * risk_multiplier
    activity_weight = activity_weight / activity_weight.sum()

    user_ids = users["user_id"].values
    chosen_users = RNG.choice(user_ids, size=n_txn, p=activity_weight)

    start = START_DATE
    end = START_DATE + timedelta(days=N_DAYS)
    txn_ts = random_dates(n_txn, start, end)

    txn_types = RNG.choice(TXN_TYPES, size=n_txn,
                           p=[0.35, 0.25, 0.25, 0.1, 0.05])

    # transaction amounts by type
    amounts = []
    for t in txn_types:
        if t == "topup":
            amt = RNG.gamma(2.0, 50)     # ~100
        elif t == "p2p_transfer":
            amt = RNG.gamma(1.5, 40)     # ~60
        elif t == "merchant_payment":
            amt = RNG.gamma(2.5, 30)     # ~75
        elif t == "withdrawal":
            amt = RNG.gamma(2.0, 80)     # ~160
        else:  # refund
            amt = RNG.gamma(1.5, 30)
        amounts.append(float(np.clip(amt, 1, 2000)))
    amounts = np.array(amounts).round(2)

    users_idx = users.set_index("user_id")
    user_countries = users_idx.loc[chosen_users, "country"].values
    user_channels = users_idx.loc[chosen_users, "channel"].values
    risk_seg = users_idx.loc[chosen_users, "risk_segment"].values

    # success/failure status
    status = RNG.choice(["success", "failed"], size=n_txn,
                        p=[0.92, 0.08])

    # fraud probability: depends on type, amount, risk segment
    base_fraud_prob = 0.003  # 0.3%
    fraud_prob = np.full(n_txn, base_fraud_prob)
    fraud_prob += np.where(np.isin(txn_types, ["p2p_transfer", "withdrawal"]), 0.002, 0.0)
    fraud_prob += np.where(amounts > 500, 0.003, 0.0)
    fraud_prob += np.where(risk_seg == "high", 0.004, 0.0)
    fraud_prob = np.clip(fraud_prob, 0, 0.15)

    is_fraud_label = RNG.binomial(1, fraud_prob)

    # chargebacks for subset of fraudulent merchant payments
    is_chargeback = np.zeros(n_txn, dtype=int)
    mask_cb = (
        (txn_types == "merchant_payment")
        & (status == "success")
        & (is_fraud_label == 1)
    )
    idx_cb = np.where(mask_cb)[0]
    if len(idx_cb) > 0:
        chosen_cb = RNG.choice(idx_cb, size=max(1, int(0.4 * len(idx_cb))), replace=False)
        is_chargeback[chosen_cb] = 1

    # counterparty: merchants for merchant_payment, other users for p2p
    merchant_ids = np.arange(1, 501)
    counterparty_id = np.full(n_txn, np.nan)
    for i, t in enumerate(txn_types):
        if t == "merchant_payment":
            counterparty_id[i] = int(RNG.choice(merchant_ids))
        elif t == "p2p_transfer":
            u = chosen_users[i]
            v = int(RNG.choice(user_ids[user_ids != u]))
            counterparty_id[i] = v

    txns = pd.DataFrame({
        "txn_id": np.arange(1, n_txn + 1),
        "user_id": chosen_users,
        "counterparty_id": counterparty_id,
        "txn_ts": txn_ts,
        "txn_date": txn_ts.date,
        "txn_type": txn_types,
        "amount": amounts,
        "currency": "SGD",
        "channel": RNG.choice(["app", "web", "api"], size=n_txn,
                              p=[0.8, 0.15, 0.05]),
        "status": status,
        "is_chargeback": is_chargeback,
        "payment_method": RNG.choice(["card", "bank", "cash_in", "promo_balance"],
                                     size=n_txn,
                                     p=[0.5, 0.3, 0.15, 0.05]),
        "country": user_countries,
        "is_fraud_label": is_fraud_label,
    })

    txns.to_csv(RAW_DIR / "transactions.csv", index=False)
    return txns


# -------------------------------------------------------------------
# 4) KYC EVENTS
# -------------------------------------------------------------------
def generate_kyc_events(users):
    rows = []
    for _, row in users.iterrows():
        uid = row["user_id"]
        signup = row["signup_date"]
        status = row["kyc_status"]

        # Submitted event
        submitted_ts = signup + timedelta(days=int(RNG.integers(0, 5)))
        rows.append({
            "event_id": None,
            "user_id": uid,
            "event_ts": submitted_ts,
            "event_type": "kyc_submitted",
            "reason_code": "",
            "doc_country": row["country"],
            "doc_type": RNG.choice(["id_card", "passport", "driver_license"]),
        })

        # Approved / rejected
        if status == "verified":
            approved_ts = submitted_ts + timedelta(days=int(RNG.integers(0, 3)))
            rows.append({
                "event_id": None,
                "user_id": uid,
                "event_ts": approved_ts,
                "event_type": "kyc_approved",
                "reason_code": "",
                "doc_country": row["country"],
                "doc_type": RNG.choice(["id_card", "passport", "driver_license"]),
            })
        elif status == "unverified" and RNG.random() < 0.3:
            rej_ts = submitted_ts + timedelta(days=int(RNG.integers(1, 5)))
            rows.append({
                "event_id": None,
                "user_id": uid,
                "event_ts": rej_ts,
                "event_type": "kyc_rejected",
                "reason_code": RNG.choice(["blurry_doc", "mismatch_name", "expired_doc"]),
                "doc_country": row["country"],
                "doc_type": RNG.choice(["id_card", "passport", "driver_license"]),
            })

    kyc = pd.DataFrame(rows)
    kyc["event_id"] = np.arange(1, len(kyc) + 1)
    kyc.to_csv(RAW_DIR / "kyc_events.csv", index=False)
    return kyc


# -------------------------------------------------------------------
# 5) LOGIN EVENTS
# -------------------------------------------------------------------
def generate_login_events(users, mapping, avg_logins_per_user_per_day=1.5):
    rows = []
    end = START_DATE + timedelta(days=N_DAYS)
    mapping_group = mapping.groupby("user_id")["device_id"].apply(list).to_dict()

    for _, row in users.iterrows():
        uid = row["user_id"]
        signup = row["signup_date"]
        if signup > end:
            continue

        active_days = (end - signup).days
        n_logins = int(RNG.poisson(avg_logins_per_user_per_day * max(active_days, 1)))
        if n_logins <= 0:
            continue

        login_ts = random_dates(n_logins, signup, end)
        device_list = mapping_group.get(uid, [None])

        for ts in login_ts:
            device_id = int(RNG.choice(device_list)) if device_list[0] is not None else np.nan

            if row["risk_segment"] == "high":
                fail_prob = 0.12
            elif row["risk_segment"] == "medium":
                fail_prob = 0.07
            else:
                fail_prob = 0.04

            login_result = "failed" if RNG.random() < fail_prob else "success"
            reason = ""
            if login_result == "failed":
                reason = RNG.choice(["wrong_password", "otp_fail", "blocked"])

            rows.append({
                "login_id": None,
                "user_id": uid,
                "device_id": device_id,
                "login_ts": ts,
                "ip_country": RNG.choice(COUNTRIES),
                "login_result": login_result,
                "reason_failure": reason,
            })

    logins = pd.DataFrame(rows)
    logins["login_id"] = np.arange(1, len(logins) + 1)
    logins.to_csv(RAW_DIR / "login_events.csv", index=False)
    return logins


# -------------------------------------------------------------------
# 6) DAILY KPIs
# -------------------------------------------------------------------
def compute_daily_kpis(transactions, users, mapping, kyc_events, login_events):
    tx = transactions.copy()
    tx["txn_date"] = pd.to_datetime(tx["txn_date"])

    # overall daily
    daily = tx.groupby("txn_date").agg(
        total_txn_count=("txn_id", "count"),
        total_txn_amount=("amount", "sum"),
        fraud_txn_count=("is_fraud_label", "sum"),
        fraud_loss_amount=("amount",
                           lambda s: s[tx.loc[s.index, "is_fraud_label"] == 1].sum()),
    ).reset_index()

    # top-up metrics
    topup = tx[tx["txn_type"] == "topup"].groupby("txn_date").agg(
        topup_count=("txn_id", "count"),
        topup_amount=("amount", "sum"),
        topup_failure_rate=("status", lambda s: (s == "failed").mean()),
    ).reset_index()

    # P2P metrics
    p2p = tx[tx["txn_type"] == "p2p_transfer"].groupby("txn_date").agg(
        p2p_count=("txn_id", "count"),
        p2p_amount=("amount", "sum"),
    ).reset_index()

    # merchant metrics
    merch = tx[tx["txn_type"] == "merchant_payment"].groupby("txn_date").agg(
        merchant_txn_count=("txn_id", "count"),
        merchant_txn_amount=("amount", "sum"),
        merchant_dispute_rate=("is_chargeback", "mean"),
    ).reset_index()

    # new users per day
    users_daily = users.copy()
    users_daily["signup_date"] = pd.to_datetime(users_daily["signup_date"]).dt.date
    new_users = (
        users_daily.groupby("signup_date")
        .agg(new_users=("user_id", "count"))
        .reset_index()
        .rename(columns={"signup_date": "txn_date"})
    )
    new_users["txn_date"] = pd.to_datetime(new_users["txn_date"])

    # KYC metrics
    kyc = kyc_events.copy()
    kyc["event_ts"] = pd.to_datetime(kyc["event_ts"])
    kyc["event_date"] = kyc["event_ts"].dt.date
    kyc_pivot = (
        kyc.pivot_table(
            index="event_date",
            columns="event_type",
            values="event_id",
            aggfunc="count",
            fill_value=0,
        )
        .reset_index()
        .rename(columns={"event_date": "txn_date"})
    )
    kyc_pivot["txn_date"] = pd.to_datetime(kyc_pivot["txn_date"])

    for col in ["kyc_submitted", "kyc_approved", "kyc_rejected"]:
        if col not in kyc_pivot.columns:
            kyc_pivot[col] = 0

    kyc_pivot["kyc_approval_rate"] = (
        kyc_pivot["kyc_approved"]
        / kyc_pivot["kyc_submitted"].replace(0, np.nan)
    )
    kyc_pivot["kyc_rejection_rate"] = (
        kyc_pivot["kyc_rejected"]
        / kyc_pivot["kyc_submitted"].replace(0, np.nan)
    )

    # login metrics
    log = login_events.copy()
    log["login_ts"] = pd.to_datetime(log["login_ts"])
    log["login_date"] = log["login_ts"].dt.date
    login_daily = (
        log.groupby("login_date")
        .agg(
            login_count=("login_id", "count"),
            failed_login_rate=("login_result", lambda s: (s == "failed").mean()),
        )
        .reset_index()
        .rename(columns={"login_date": "txn_date"})
    )
    login_daily["txn_date"] = pd.to_datetime(login_daily["txn_date"])

    # multi-account device rate (approx, based on first_seen)
    mapping_copy = mapping.copy()
    mapping_copy["first_seen_ts"] = pd.to_datetime(mapping_copy["first_seen_ts"])
    mapping_copy["first_seen_date"] = mapping_copy["first_seen_ts"].dt.date

    users_per_device = (
        mapping_copy.groupby("device_id")["user_id"]
        .nunique()
        .reset_index(name="user_count")
    )
    
    risky_devices = users_per_device[users_per_device["user_count"] >= 3]["device_id"].tolist()
    mapping_copy["is_multi_account_device"] = mapping_copy["device_id"].isin(risky_devices)

    multi_daily = (
        mapping_copy.groupby("first_seen_date")
        .agg(
            multi_account_devices=("is_multi_account_device", "sum"),
            total_devices=("device_id", "nunique"),
        )
        .reset_index()
        .rename(columns={"first_seen_date": "txn_date"})
    )
    multi_daily["txn_date"] = pd.to_datetime(multi_daily["txn_date"])
    multi_daily["multi_account_device_rate"] = (
        multi_daily["multi_account_devices"]
        / multi_daily["total_devices"].replace(0, np.nan)
    )

    # merge all metrics
    daily_metrics = (
        daily
        .merge(topup, on="txn_date", how="left")
        .merge(p2p, on="txn_date", how="left")
        .merge(merch, on="txn_date", how="left")
        .merge(new_users, on="txn_date", how="left")
        .merge(kyc_pivot, on="txn_date", how="left")
        .merge(login_daily, on="txn_date", how="left")
        .merge(multi_daily, on="txn_date", how="left")
        .sort_values("txn_date")
    )

    daily_metrics.fillna(0, inplace=True)

    daily_metrics["fraud_txn_rate"] = (
        daily_metrics["fraud_txn_count"]
        / daily_metrics["total_txn_count"].replace(0, np.nan)
    )

    daily_metrics.to_csv(PROCESSED_DIR / "daily_risk_metrics.csv", index=False)
    return daily_metrics


# -------------------------------------------------------------------
# 7) ANOMALY FLAGS
# -------------------------------------------------------------------
def add_anomaly_flags(daily_metrics):
    metrics_to_flag = [
        "fraud_loss_amount",
        "fraud_txn_rate",
        "multi_account_device_rate",
        "failed_login_rate",
        "merchant_dispute_rate",
        "topup_failure_rate",
        "kyc_rejection_rate",
    ]

    df = daily_metrics.copy().sort_values("txn_date")

    for col in metrics_to_flag:
        if col not in df.columns:
            continue

        series = df[col].astype(float)
        rolling_mean = series.rolling(window=7, min_periods=5).mean()
        rolling_std = series.rolling(window=7, min_periods=5).std()

        z = (series - rolling_mean) / rolling_std.replace(0, np.nan)
        delta_pct = (series - rolling_mean) / rolling_mean.replace(0, np.nan)

        df[f"{col}_zscore"] = z
        df[f"{col}_delta_pct"] = delta_pct

        cond = (z.abs() >= 2) & (delta_pct.abs() >= 0.3)
        df[f"{col}_is_anomaly"] = cond.astype(int)

    df.to_csv(PROCESSED_DIR / "daily_risk_metrics_with_anomalies.csv", index=False)
    return df


# -------------------------------------------------------------------
# MAIN
# -------------------------------------------------------------------
def main():
    print("Generating synthetic digital wallet risk dataset...")
    users = generate_users()
    devices = generate_devices()
    mapping = generate_user_device_mapping(users, devices)
    txns = generate_transactions(users, mapping)
    kyc_events = generate_kyc_events(users)
    login_events = generate_login_events(users, mapping)
    daily = compute_daily_kpis(txns, users, mapping, kyc_events, login_events)
    _ = add_anomaly_flags(daily)
    print("Done.")
    print(f"Raw data saved to: {RAW_DIR}")
    print(f"Daily metrics saved to: {PROCESSED_DIR}")


if __name__ == "__main__":
    main()

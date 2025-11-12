"""
generate_synthetic_data.py
----------------------------------
Creates synthetic AML datasets for analytics prototyping:

- clients.csv            (KYC-style attributes)
- transactions.csv       (with injected suspicious archetypes)
- country_risk.csv       (toy reference table)

USAGE
-----
python generate_synthetic_data.py \
  --outdir ./data \
  --clients 2000 \
  --transactions 50000 \
  --seed 42 \
  --start 2024-01-01 \
  --end 2025-10-31

PARAMETERS
----------
--outdir         Output directory (created if missing). Default: ./data
--clients        Number of synthetic clients. Default: 2000
--transactions   Number of synthetic transactions. Default: 50000
--seed           Base random seed. Default: 42
--start          Start date (YYYY-MM-DD). Default: 2024-01-01
--end            End date (YYYY-MM-DD). Default: 2025-10-31

NOTES
-----
- Transactions include injected suspicious patterns (e.g., high-value wires to
  high-risk countries, rapid in/out, cash structuring/smurfing, bursts, high
  geographic diversity). The column `label_suspicious_injected` is for your
  validation ONLY; do not use it during model training in realistic settings.
"""

import argparse
from datetime import datetime, timedelta
from pathlib import Path
import numpy as np
import pandas as pd


# -------------------------------
# Reference: toy country risk
# -------------------------------
def build_country_risk() -> pd.DataFrame:
    return pd.DataFrame({
        "country": [
            "SG","CH","US","GB","DE","FR","AU","JP","HK","AE",
            "ID","MY","PH","VN","TH","IN","CN","NG","RU","UA",
            "IR","IQ","AF","PK","VE","CU"
        ],
        "risk_score": [
            5,5,6,6,5,5,5,5,6,7,
            6,6,7,6,6,6,6,9,8,7,
            10,9,10,8,8,9
        ],  # 10 = highest
        "is_high_risk": [
            0,0,0,0,0,0,0,0,0,1,
            0,0,1,0,0,0,0,1,1,1,
            1,1,1,1,1,1
        ]
    })


# -------------------------------
# Clients
# -------------------------------
def generate_clients(n_clients: int = 2000, seed: int = 123) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    first = ["Alex","Taylor","Jordan","Casey","Morgan","Jamie","Riley","Sam","Chris","Avery","Dana","Evan","Kai","Lee","Noel","Parker","Quinn"]
    last  = ["Tan","Lim","Ng","Wong","Lee","Smith","Chen","Yamada","Khan","Garcia","Müller","Dubois","Ivanov","Johnson","Singh","Novak","Rossi"]
    occupations = ["Executive","Entrepreneur","Engineer","Consultant","Doctor","Lawyer","Trader","Investor",
                   "Real Estate","Tech Founder","Importer-Exporter","Philanthropist","Fund Manager","Artist"]
    sources_of_funds = ["Salary","Business Proceeds","Investment Income","Inheritance","Property Sale","Dividends"]

    # Private-banking-ish mix
    base_cty = ["SG","CH","HK","US","GB","DE","FR","AE","JP","AU","ID","MY","PH","VN","TH","IN","CN","RU","NG"]
    probs = np.array([0.14,0.12,0.10,0.10,0.08,0.05,0.04,0.04,0.04,0.04,0.05,0.04,0.03,0.03,0.03,0.03,0.03,0.02,0.01])
    probs = probs / probs.sum()

    names = [f"{rng.choice(first)} {rng.choice(last)}" for _ in range(n_clients)]
    resid = rng.choice(base_cty, size=n_clients, p=probs)
    pep = (rng.random(n_clients) < 0.015).astype(int)  # ~1.5% PEP
    birth_year = rng.integers(1945, 2001, size=n_clients)

    # Onboard between 2016 and 2024
    start = datetime(2016,1,1)
    onboard_days = rng.integers(0, 365*9, size=n_clients)
    onboard = [(start + timedelta(days=int(d))).date().isoformat() for d in onboard_days]

    occ = rng.choice(occupations, size=n_clients)
    sof = rng.choice(sources_of_funds, size=n_clients)
    base_bal = np.round(rng.lognormal(mean=11.2, sigma=0.8, size=n_clients), 2)  # skewed wealth

    clients = pd.DataFrame({
        "client_id": np.arange(1, n_clients+1, dtype=int),
        "client_name": names,
        "residency_country": resid,
        "pep_flag": pep,
        "birth_year": birth_year,
        "onboard_date": onboard,
        "occupation": occ,
        "source_of_funds": sof,
        "starting_balance_usd": base_bal
    })
    return clients


# -------------------------------
# Transactions with archetypes
# -------------------------------
def generate_transactions(
    clients_df: pd.DataFrame,
    n_tx: int = 50000,
    start_date: str = "2024-01-01",
    end_date: str = "2025-10-31",
    seed: int = 456
) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    start = datetime.fromisoformat(start_date)
    end   = datetime.fromisoformat(end_date)
    days = (end - start).days

    country_risk = build_country_risk()
    high_risk = country_risk[country_risk.is_high_risk==1].country.values
    channels = np.array(["wire","swift","local","cash","crypto"])
    p_channels = np.array([0.45,0.25,0.15,0.08,0.07])
    tx_types = np.array(["deposit","withdrawal","transfer","payment","fx"])
    currencies = np.array(["USD","EUR","GBP","CHF","SGD","HKD","JPY","AUD"])

    # Pre-maps and per-client behavior
    resid_map = dict(zip(clients_df["client_id"].values, clients_df["residency_country"].values))
    client_ids = clients_df["client_id"].values
    # behavior per client
    avg_amt = np.clip(rng.lognormal(10.5, 0.7, size=len(client_ids)), 1000, 500000)
    intl_share = np.clip(rng.normal(0.35, 0.2, size=len(client_ids)), 0.0, 0.95)
    diversity = np.clip(rng.normal(4,2, size=len(client_ids)).astype(int), 1, 12)
    behav = {int(cid):(float(a), float(i), int(d)) for cid,a,i,d in zip(client_ids, avg_amt, intl_share, diversity)}

    # Mark a subset as suspicious archetypes
    sus_set = set(rng.choice(client_ids, size=max(1, int(len(client_ids)*0.06)), replace=False))
    archetypes = np.array(["high_value_to_hrc","rapid_in_out","smurfing","burst_activity","high_geo_diversity"])
    arche_map = {int(cid): str(rng.choice(archetypes)) for cid in sus_set}

    # Base arrays for speed
    cids = rng.choice(client_ids, size=n_tx)
    day_offsets = rng.integers(0, max(1, days), size=n_tx)  # robust if start==end
    seconds = rng.integers(0, 86400, size=n_tx)
    cr_probs = country_risk["risk_score"].values / country_risk["risk_score"].values.sum()

    rows = []
    for i in range(n_tx):
        cid = int(cids[i])
        ts = start + timedelta(days=int(day_offsets[i]), seconds=int(seconds[i]))
        a, ishare, div = behav[cid]

        # base amount ~ lognormal around client avg
        amount = float(np.round(np.exp(rng.normal(np.log(a), 0.6)), 2))

        # counterparty
        resid = resid_map[cid]
        if rng.random() < ishare:
            cty = str(rng.choice(country_risk["country"].values, p=cr_probs))
        else:
            cty = resid if rng.random() < 0.8 else str(rng.choice(["SG","HK","JP","US","GB","CH"]))

        channel = str(rng.choice(channels, p=p_channels))
        ttype   = str(rng.choice(tx_types))
        curr    = str(rng.choice(currencies))
        direction = str(rng.choice(["in","out"], p=[0.45,0.55]))
        is_intl = int(cty != resid)
        label = 0

        # Inject archetype behavior
        r = rng.random()
        if cid in arche_map:
            at = arche_map[cid]
            if at == "high_value_to_hrc" and r < 0.35:
                amount = float(np.round(a * rng.uniform(3.5, 12.0), 2))
                cty = str(rng.choice(high_risk))
                channel = "swift"; ttype = "transfer"; direction = "out"; label = 1
            elif at == "rapid_in_out" and r < 0.30:
                ts = ts.replace(hour=int(rng.integers(8, 18)), minute=int(rng.integers(0,60)))
                amount = float(np.round(a * rng.uniform(0.5, 2.0), 2))
                ttype = "transfer"
                direction = str(rng.choice(["in","out"]))
                label = int(rng.random() < 0.6)
            elif at == "smurfing" and (channel == "cash" or r < 0.3):
                channel = "cash"
                amount = float(np.round(rng.uniform(8000, 9990), 2))  # <10k
                label = int(rng.random() < 0.5)
            elif at == "burst_activity" and r < 0.28:
                ts = ts.replace(hour=int(rng.integers(9, 17)))
                amount = float(np.round(a * rng.uniform(1.2, 4.0), 2))
                ttype = "payment"
                label = int(amount > a * 1.8)
            elif at == "high_geo_diversity" and r < 0.4:
                cty = str(rng.choice(country_risk["country"].values))
                label = int(country_risk.set_index("country").loc[cty, "is_high_risk"]==1 and rng.random()<0.5)

        rows.append((
            i+1, cid, ts.isoformat(sep=" "), amount, curr, channel, ttype, direction, cty, is_intl, label
        ))

    tx = pd.DataFrame(rows, columns=[
        "tx_id","client_id","ts","amount_usd","currency","channel","tx_type","direction",
        "counterparty_country","is_international","label_suspicious_injected"
    ]).sort_values("ts").reset_index(drop=True)

    return tx


# -------------------------------
# Main
# -------------------------------
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--outdir", default="./data")
    ap.add_argument("--clients", type=int, default=2000)
    ap.add_argument("--transactions", type=int, default=50000)
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--start", default="2024-01-01")
    ap.add_argument("--end", default="2025-10-31")
    args = ap.parse_args()

    outdir = Path(args.outdir)
    outdir.mkdir(parents=True, exist_ok=True)

    # Build data
    clients = generate_clients(n_clients=args.clients, seed=args.seed)
    tx = generate_transactions(
        clients_df=clients,
        n_tx=args.transactions,
        start_date=args.start,
        end_date=args.end,
        seed=args.seed + 1
    )
    cr = build_country_risk()

    # Save
    clients.to_csv(outdir / "clients.csv", index=False)
    tx.to_csv(outdir / "transactions.csv", index=False)
    cr.to_csv(outdir / "country_risk.csv", index=False)

    print(f"Wrote: {outdir/'clients.csv'}")
    print(f"Wrote: {outdir/'transactions.csv'}")
    print(f"Wrote: {outdir/'country_risk.csv'}")


if __name__ == "__main__":
    main()



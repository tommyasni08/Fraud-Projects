
"""
feature_engineering.py (robust)
Builds AML features with safe per-client time-based rolling that avoids
"ValueError: cannot reindex on an axis with duplicate labels" across Pandas versions.
"""
import pandas as pd
import numpy as np

def parse_dates(df, col="ts"):
    df = df.copy()
    df[col] = pd.to_datetime(df[col])
    df = df.sort_values(["client_id", col])
    return df

def add_basic_flags(tx: pd.DataFrame, country_risk: pd.DataFrame) -> pd.DataFrame:
    tx = tx.copy()
    risk_map = country_risk.set_index("country")["risk_score"].to_dict()
    hr_map = country_risk.set_index("country")["is_high_risk"].to_dict()
    tx["counterparty_risk"] = tx["counterparty_country"].map(risk_map).fillna(5)
    tx["counterparty_is_high_risk"] = tx["counterparty_country"].map(hr_map).fillna(0).astype(int)
    tx["is_large_tx_abs"] = (tx["amount_usd"] >= 100000).astype(int)
    tx["is_cash"] = (tx["channel"]=="cash").astype(int)
    tx["is_swift"] = (tx["channel"]=="swift").astype(int)
    tx["is_transfer"] = (tx["tx_type"]=="transfer").astype(int)
    return tx

def _safe_time_roll(group: pd.DataFrame, windows=("1D","7D","30D")) -> pd.DataFrame:
    """Compute time-based rolling per client using a temporary DatetimeIndex,
    returning arrays aligned to the original row order. Robust to duplicate labels.
    """
    g = group.sort_values("ts").copy()
    g_idxed = g.set_index("ts")
    out = g.copy()
    for win in windows:
        cnt = g_idxed["tx_id"].rolling(win).count().to_numpy(dtype=float)
        ssum = g_idxed["amount_usd"].rolling(win).sum().to_numpy(dtype=float)
        mean = g_idxed["amount_usd"].rolling(win).mean().to_numpy(dtype=float)
        hrc = g_idxed["counterparty_is_high_risk"].rolling(win).sum().to_numpy(dtype=float)
        cash = g_idxed["is_cash"].rolling(win).sum().to_numpy(dtype=float)
        swift = g_idxed["is_swift"].rolling(win).sum().to_numpy(dtype=float)
        out[f"roll_cnt_{win}"] = cnt
        out[f"roll_amt_sum_{win}"] = ssum
        out[f"roll_amt_mean_{win}"] = mean
        out[f"roll_hrc_cnt_{win}"] = hrc
        out[f"roll_cash_cnt_{win}"] = cash
        out[f"roll_swift_cnt_{win}"] = swift
    # z-score per client
    amt = out["amount_usd"].astype(float)
    mu = amt.mean()
    sd = amt.std(ddof=0)
    z = (amt - mu) / (sd if sd != 0 else 1.0)
    out["amt_z"] = z.clip(-5, 10)
    return out

def rolling_features(tx: pd.DataFrame, windows=("1D","7D","30D")) -> pd.DataFrame:
    # apply per client to avoid reindex errors
    parts = []
    for _, g in tx.groupby("client_id", sort=False):
        parts.append(_safe_time_roll(g, windows))
    out = pd.concat(parts, axis=0, ignore_index=True)
    return out

def build_features(transactions: pd.DataFrame, country_risk: pd.DataFrame) -> pd.DataFrame:
    tx = parse_dates(transactions)
    tx = add_basic_flags(tx, country_risk)
    feats = rolling_features(tx)
    return feats

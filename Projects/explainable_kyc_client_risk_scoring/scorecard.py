"""KYC risk scorecard: rule-based, explainable scoring with watchlist enrichment."""
from __future__ import annotations
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, Any, Tuple
import yaml
from difflib import SequenceMatcher

def load_config(path: str | Path) -> Dict[str, Any]:
    with open(path, "r") as f:
        return yaml.safe_load(f)

def occupation_to_group(occupation: str) -> str:
    if not isinstance(occupation, str):
        return "Other"
    oc = occupation.lower()
    cash_intensive_keywords = ["real estate", "importer", "export", "trader", "retail"]
    if any(k in oc for k in cash_intensive_keywords):
        return "Cash_Intensive"
    if "fund" in oc or "investor" in oc or "trader" in oc:
        return "Financial_Markets"
    return "Other"

def compute_tenure_days(onboard_date: pd.Series, as_of: pd.Timestamp) -> pd.Series:
    od = pd.to_datetime(onboard_date, errors="coerce")
    return (as_of - od).dt.days

def best_fuzzy_match(name: str, watchlist: pd.DataFrame) -> Tuple[float, Any]:
    if not isinstance(name, str) or name.strip() == "" or watchlist.empty:
        return 0.0, None
    name_norm = name.lower().strip()
    best_score = 0.0
    best_row = None
    for _, row in watchlist.iterrows():
        for col in ["name", "alias_1", "alias_2"]:
            cand = str(row.get(col, "")).strip()
            if not cand:
                continue
            score = SequenceMatcher(None, name_norm, cand.lower()).ratio()
            if score > best_score:
                best_score = score
                best_row = row
    return best_score, best_row

def enrich_watchlist(clients: pd.DataFrame, watchlist: pd.DataFrame, cfg: Dict[str, Any]) -> pd.DataFrame:
    wl = watchlist.copy()
    df = clients.copy()
    thresh = cfg.get("fuzzy_match", {}).get("similarity_threshold", 0.88)
    enabled = cfg.get("fuzzy_match", {}).get("enabled", True)

    pep_match = []
    sanc_match = []
    best_sim = []

    for _, row in df.iterrows():
        nm = row.get("client_name", "")
        m = wl[wl["name"].str.lower() == str(nm).lower()]
        pep = 0
        sanc = 0
        sim = 0.0
        if not m.empty:
            if (m["type"] == "PEP").any():
                pep = 1
                sim = 1.0
            if (m["type"] == "SANCTION").any():
                sanc = 1
                sim = 1.0
        elif enabled:
            sim, best_row = best_fuzzy_match(str(nm), wl)
            if best_row is not None and sim >= thresh:
                if best_row.get("type") == "PEP":
                    pep = 1
                if best_row.get("type") == "SANCTION":
                    sanc = 1
        pep_match.append(pep)
        sanc_match.append(sanc)
        best_sim.append(sim)

    df["pep_match"] = pep_match
    df["sanction_match"] = sanc_match
    df["name_similarity"] = best_sim
    return df

def apply_scorecard(features: pd.DataFrame, cfg: Dict[str, Any]) -> pd.DataFrame:
    w = cfg.get("weights", {})
    thr = cfg.get("thresholds", {})
    tiers_cfg = cfg.get("tiers", {})
    high_cut = tiers_cfg.get("high", 55)
    med_cut = tiers_cfg.get("medium", 30)

    df = features.copy()
    scores = []
    factors = []

    for _, row in df.iterrows():
        s = 0.0
        f = []

        if row.get("pep_flag", 0) == 1:
            s += w.get("pep_flag", 0); f.append("PEP flag")
        if row.get("pep_match", 0) == 1:
            s += w.get("pep_match", 0); f.append("Watchlist PEP match")
        if row.get("sanction_match", 0) == 1:
            s += w.get("sanction_match", 0); f.append("Watchlist sanction match")

        if row.get("residency_country_is_high", 0) == 1:
            s += w.get("residency_country_high", 0); f.append("High-risk residency")


        if row.get("occupation_group") == "Cash_Intensive":
            s += w.get("occupation_cash_intensive", 0); f.append("Cash-intensive occupation")


        if row.get("intl_rate_90d", 0.0) > thr.get("intl_rate_90d_high", 0.5):
            s += w.get("intl_rate_90d_high", 0); f.append("High cross-border activity (90d)")


        if row.get("hrc_hits_90d", 0) >= 2:
            s += w.get("hrc_hits_90d_ge_2", 0); f.append("Multiple HRC counterparties (90d)")


        if row.get("swift_out_90d", 0) >= 2:
            s += w.get("swift_out_90d_ge_2", 0); f.append("Multiple SWIFT out wires (90d)")


        if row.get("cash_structuring_hits_30d", 0) >= 2:
            s += w.get("cash_structuring_hits_30d_ge_2", 0); f.append("Cash structuring pattern (30d)")


        if row.get("large_value_rate_180d", 0.0) >= thr.get("large_value_rate_180d_high", 0.2):
            s += w.get("large_value_rate_180d_high", 0); f.append("High share of large-value tx (180d)")


        if row.get("geo_diversity_180d", 0) >= thr.get("geo_diversity_180d_high", 8):
            s += w.get("geo_diversity_180d_high", 0); f.append("High geographic diversity (180d)")

        scores.append(s)
        factors.append(", ".join(f))

    df["risk_score"] = scores
    df["top_factors"] = factors

    def tier(s):
        if s >= high_cut:
            return "High"
        if s >= med_cut:
            return "Medium"
        return "Low"

    df["risk_tier"] = df["risk_score"].apply(tier)
    return df

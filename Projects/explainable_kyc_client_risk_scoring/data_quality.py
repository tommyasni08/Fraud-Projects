"""Data quality checks for KYC risk scoring."""
from __future__ import annotations
import pandas as pd
import numpy as np

def run_data_quality(clients: pd.DataFrame, country_risk: pd.DataFrame) -> pd.Series:
    """Return a qc_flags string per client_id summarising simple data quality issues."""
    df = clients.copy()
    valid_countries = set(country_risk["country"].astype(str).unique())
    flags = {cid: [] for cid in df["client_id"].tolist()}

    for _, row in df.iterrows():
        cid = row["client_id"]
        # Birth year
        by = row.get("birth_year", np.nan)
        if pd.isna(by) or by < 1900 or by > 2025:
            flags[cid].append("birth_year_invalid")
        # Onboard date
        od = row.get("onboard_date", None)
        try:
            pd.to_datetime(od)
        except Exception:
            flags[cid].append("onboard_date_invalid")
        # Country
        rc = str(row.get("residency_country", "")).upper()
        if rc not in valid_countries:
            flags[cid].append("residency_country_unknown")
        # PEP flag
        pf = row.get("pep_flag", None)
        if pd.isna(pf):
            flags[cid].append("pep_flag_missing")

    out = {}
    for cid, f in flags.items():
        out[cid] = ",".join(sorted(set(f))) if f else ""
    return pd.Series(out, name="qc_flags")

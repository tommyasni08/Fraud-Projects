#!/usr/bin/env python
import numpy as np
import pandas as pd

def uplift_at_k(df, uplift_col, outcome_col, k=0.3):
    df = df.dropna(subset=[uplift_col, outcome_col]).copy()
    df = df.sort_values(uplift_col, ascending=False)
    n = max(1, int(len(df)*k))
    top = df.head(n)[outcome_col].mean()
    rest = df.tail(n)[outcome_col].mean() if len(df) >= 2*n else df[outcome_col].mean()
    return float(top - rest)

def qini_approx(df, uplift_col, treatment_flag_col, outcome_col, bins=10):
    tmp = df.dropna(subset=[uplift_col, outcome_col, treatment_flag_col]).copy()
    tmp["bucket"] = pd.qcut(tmp[uplift_col].rank(pct=True), bins, labels=False, duplicates="drop")
    curve = (tmp.groupby("bucket")
                .apply(lambda g: g.loc[g[treatment_flag_col]==1, outcome_col].mean() - tmp[outcome_col].mean())
                .fillna(0.0))
    auuc = float(np.trapz(curve.values))
    return auuc, curve.values.tolist()

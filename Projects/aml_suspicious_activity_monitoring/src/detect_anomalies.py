import pandas as pd
import numpy as np
from sklearn.ensemble import IsolationForest

RULES = [
    ("large_value", lambda df: df["amount_usd"] >= 100000, 2.0),
    ("swift_out_high_risk", lambda df: (df["is_swift"]==1)&(df["direction"]=="out")&(df["counterparty_is_high_risk"]==1), 3.0),
    ("cash_structuring", lambda df: (df["is_cash"]==1)&(df["amount_usd"].between(8000, 9999)), 1.5),
    ("amount_spike", lambda df: df["amt_z"] >= 3.0, 2.0),
    ("burst_activity_7d", lambda df: df["roll_cnt_7D"] >= 10, 1.5),
    ("hrc_exposure_30d", lambda df: df["roll_hrc_cnt_30D"] >= 3, 1.8),
]

def apply_rules(feats: pd.DataFrame) -> pd.DataFrame:
    out = feats.copy()
    score = np.zeros(len(out), dtype=float)
    for name, fn, w in RULES:
        mask = fn(out).astype(int)
        out[f"rule__{name}"] = mask
        score += w * mask
    out["rule_score"] = score
    return out

def isolation_forest_scores(feats: pd.DataFrame, feature_cols=None, random_state=42):
    if feature_cols is None:
        feature_cols = [
            "amount_usd","amt_z",
            "roll_cnt_1D","roll_cnt_7D","roll_cnt_30D",
            "roll_amt_sum_7D","roll_amt_sum_30D",
            "roll_hrc_cnt_7D","roll_hrc_cnt_30D",
            "roll_cash_cnt_7D","roll_swift_cnt_7D",
            "counterparty_risk","is_international","is_cash","is_swift","is_transfer"
        ]
    X = feats[feature_cols].fillna(0.0).values
    clf = IsolationForest(n_estimators=200, contamination="auto", random_state=random_state)
    clf.fit(X)
    scores = -clf.score_samples(X)
    return pd.Series(scores, index=feats.index, name="iforest_score")

def combine_scores(scored_df: pd.DataFrame, alpha=0.6) -> pd.DataFrame:
    out = scored_df.copy()
    out["hybrid_score"] = alpha*out["iforest_score"] + (1-alpha)*out["rule_score"]
    return out

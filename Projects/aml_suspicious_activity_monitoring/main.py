import pandas as pd
from pathlib import Path
from src.feature_engineering import build_features
from src.detect_anomalies import apply_rules, isolation_forest_scores, combine_scores

base_dir = Path(__file__).resolve().parent

tx = pd.read_csv(base_dir / "data/transactions.csv")
cr = pd.read_csv(base_dir / "data/country_risk.csv")

feats = build_features(tx, cr)
scored = apply_rules(feats)
scored["iforest_score"] = isolation_forest_scores(scored)
final = combine_scores(scored)
top_flags = final.sort_values("hybrid_score", ascending=False).head(25)
top_flags[["client_id","ts","amount_usd","channel","direction","counterparty_country","rule_score","iforest_score","hybrid_score"]]

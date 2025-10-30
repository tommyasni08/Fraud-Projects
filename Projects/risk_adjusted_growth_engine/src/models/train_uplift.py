#!/usr/bin/env python
import argparse, os, joblib
import pandas as pd
import numpy as np
from pathlib import Path
from sklearn.model_selection import train_test_split
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.metrics import mean_absolute_error

# Directory of the current file
base_dir = Path(__file__).resolve().parents[2]

ARMS = ["control","education_nudge","personalized_reco","reco_small_bonus"]
TARGET = "net_revenue"

def select_features(df):
    drop_cols = {"user_id","week","week_start","risk_tier","arm","dep_increase_7d","fraud_flag_14d","abuse_flag_14d","net_revenue"}
    feats = [c for c in df.columns if c not in drop_cols and not c.startswith("arm__")]
    feats = [c for c in feats if pd.api.types.is_numeric_dtype(df[c])]
    return feats

def train_arm(df, arm, features):
    d = df[df["arm"]==arm].copy()
    d = d.dropna(subset=[TARGET])
    if len(d) < 20:
        raise RuntimeError(f"Not enough rows for arm={arm} ({len(d)})")
    X = d[features].fillna(0.0).values
    y = d[TARGET].values
    Xtr, Xte, ytr, yte = train_test_split(X, y, test_size=0.2, random_state=42)
    model = GradientBoostingRegressor(random_state=42)
    model.fit(Xtr, ytr)
    mae = mean_absolute_error(yte, model.predict(Xte))
    return model, mae

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--features', required=True)
    ap.add_argument('--out', required=True)
    ap.add_argument('--min_week', type=int, default=0)
    args = ap.parse_args()

    out_path = base_dir / args.out
    features_path = base_dir / args.features

    os.makedirs(out_path, exist_ok=True)
    pred_dir = os.path.join(out_path, 'predictions'); os.makedirs(pred_dir, exist_ok=True)
    model_dir = os.path.join(out_path, 'models'); os.makedirs(model_dir, exist_ok=True)

    df = pd.read_csv(features_path)
    df = df[df['week']>=args.min_week].copy()
    features = select_features(df)

    metrics = {}
    models = {}
    for arm in ARMS:
        try:
            m, mae = train_arm(df, arm, features)
            joblib.dump(m, os.path.join(model_dir, f'model_{arm}.pkl'))
            models[arm] = m
            metrics[arm] = {'MAE': float(mae)}
        except Exception as e:
            metrics[arm] = {'error': str(e)}

    Xfull = df[features].fillna(0.0).values
    for arm, m in models.items():
        df[f"yhat_{arm}"] = m.predict(Xfull)
    if "yhat_control" in df.columns:
        for arm in ARMS:
            if arm != "control" and f"yhat_{arm}" in df.columns:
                df[f"uplift_vs_control__{arm}"] = df[f"yhat_{arm}"] - df["yhat_control"] - df.get("bonus_cost", 0.0)
    yhat_cols = [c for c in df.columns if c.startswith("yhat_")]
    if yhat_cols:
        df["best_arm_naive"] = pd.Series(yhat_cols, index=yhat_cols)
        df["best_arm_naive"] = df[yhat_cols].idxmax(axis=1).str.replace("yhat_","",regex=False)
    keep = ["user_id","week","arm","net_revenue","bonus_cost"] + [c for c in df.columns if c.startswith("yhat_") or c.startswith("uplift_vs_control__")] + ["best_arm_naive"]
    df[keep].to_csv(os.path.join(pred_dir, "uplift_predictions.csv"), index=False)

    with open(os.path.join(out_path, "uplift_training_report.json"), "w") as f:
        import json; json.dump({"per_arm":metrics, "n_rows":int(len(df)), "n_features":len(features)}, f, indent=2)
    print("Done training uplift.")

if __name__ == "__main__":
    main()

    # "args": [
    #     "--features",
    #     "data/processed/features_user_week.csv",
    #     "--out",
    #     "artifacts",
    #     "--min_week",
    #     "0"
    #   ]

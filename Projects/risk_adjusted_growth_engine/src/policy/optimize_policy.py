#!/usr/bin/env python
import argparse, os, json
import numpy as np
import pandas as pd
from pathlib import Path

# Directory of the current file
base_dir = Path(__file__).resolve().parents[2]

ARMS = ["control","education_nudge","personalized_reco","reco_small_bonus"]

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--features', required=True)
    ap.add_argument('--uplift', required=True)
    ap.add_argument('--risk', required=True)
    ap.add_argument('--out', required=True)
    ap.add_argument('--lambda_risk', type=float, default=2.0)
    ap.add_argument('--max_avg_risk', type=float, default=0.08)
    ap.add_argument('--max_avg_bonus', type=float, default=0.50)
    args = ap.parse_args()

    features_path = base_dir / args.features
    uplift_path = base_dir / args.uplift
    risk_path = base_dir / args.risk
    out_path = base_dir / args.out

    os.makedirs(out_path, exist_ok=True)
    pred_dir = os.path.join(out_path, 'predictions'); os.makedirs(pred_dir, exist_ok=True)

    feat = pd.read_csv(features_path)
    upl = pd.read_csv(uplift_path)
    risk = pd.read_csv(risk_path)

    df = upl.merge(feat[['user_id','week','arm','bonus_cost','net_revenue']], on=['user_id','week','arm'], how='left')
    df = df.merge(risk[['user_id','week','risk_blend']], on=['user_id','week'], how='left')
    df['risk_blend'] = df['risk_blend'].fillna(df['risk_blend'].median())

    yhat_cols = [c for c in df.columns if c.startswith('yhat_')]
    for col in yhat_cols:
        arm = col.replace('yhat_','')
        df[f'util_{arm}'] = df[col] - args.lambda_risk*df['risk_blend'] - (0.5 if arm=='reco_small_bonus' else 0.0)

    util_cols = [c for c in df.columns if c.startswith('util_')]
    df['arm_choice'] = df[util_cols].idxmax(axis=1).str.replace('util_','',regex=False)

    # Constraint repair loop
    chosen = df.copy()
    chosen['chosen_bonus_cost'] = (chosen['arm_choice']=='reco_small_bonus').astype(float)*0.5
    for _ in range(1000):
        avg_risk = float(chosen['risk_blend'].mean())
        avg_bonus = float(chosen['chosen_bonus_cost'].mean())
        if avg_risk <= args.max_avg_risk and avg_bonus <= args.max_avg_bonus:
            break
        # Move the highest-risk bonus allocation to a safer non-bonus arm
        mask = (chosen['arm_choice']=='reco_small_bonus')
        if not mask.any(): break
        idx = chosen.loc[mask, 'risk_blend'].idxmax()
        row = chosen.loc[idx]
        candidates = ['personalized_reco','education_nudge','control']
        best = max(candidates, key=lambda a: row.get(f'util_{a}', -1e9))
        chosen.at[idx,'arm_choice'] = best
        chosen.at[idx,'chosen_bonus_cost'] = 0.0

    out_path_res = os.path.join(pred_dir, 'policy_recommendations.csv')
    keep = ['user_id','week','arm_choice','risk_blend','chosen_bonus_cost'] + yhat_cols + util_cols
    chosen[keep].to_csv(out_path_res, index=False)

    report = {
        'lambda_risk': args.lambda_risk,
        'max_avg_risk': args.max_avg_risk,
        'max_avg_bonus': args.max_avg_bonus,
        'final_avg_risk': float(chosen['risk_blend'].mean()),
        'final_avg_bonus': float(chosen['chosen_bonus_cost'].mean()),
        'arm_distribution': chosen['arm_choice'].value_counts(normalize=True).to_dict(),
        'rows': int(len(chosen))
    }
    with open(os.path.join(out_path,'policy_report.json'), 'w') as f:
        json.dump(report, f, indent=2)
    print(json.dumps(report, indent=2))

if __name__ == '__main__':
    main()

    # "args": [
    #     "--features",
    #     "data/processed/features_user_week.csv",
    #     "--uplift",
    #     "artifacts/predictions/uplift_predictions.csv",
    #     "--risk",
    #     "artifacts/predictions/risk_scores.csv",
    #     "--out",
    #     "artifacts",
    #     "--lambda_risk",
    #     "2.0",
    #     "--max_avg_risk",
    #     "0.08",
    #     "--max_avg_bonus",
    #     "0.50"
    #   ]

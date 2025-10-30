#!/usr/bin/env python
import argparse, os, json, pandas as pd, sys
from pathlib import Path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))
from src.metrics.uplift_metrics import uplift_at_k, qini_approx

# Directory of the current file
base_dir = Path(__file__).resolve().parents[2]

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--features', required=True)
    ap.add_argument('--uplift', required=True)
    ap.add_argument('--out', required=True)
    args = ap.parse_args()

    out_path = base_dir / args.out
    features_path = base_dir / args.features
    uplift_path = base_dir / args.uplift

    os.makedirs(out_path, exist_ok=True)
    feat = pd.read_csv(features_path)
    upl = pd.read_csv(uplift_path)
    df = upl.merge(
        feat[['user_id','week','net_revenue','arm']],
        on=['user_id','week','arm'],
        how='left',
        suffixes=('_pred', '_true')
    )

    # Keep only the true outcome
    if 'net_revenue_true' in df.columns:
        df.drop(columns=['net_revenue_pred'], errors='ignore', inplace=True)
        df.rename(columns={'net_revenue_true': 'net_revenue'}, inplace=True)


    col = 'uplift_vs_control__personalized_reco'
    uatk = None; auuc=None; curve=[]
    if col in df.columns:
        uatk = uplift_at_k(df, col, 'net_revenue', k=0.3)
        df['treat_flag'] = (df['arm']=='personalized_reco').astype(int)
        auuc, curve = qini_approx(df, col, 'treat_flag', 'net_revenue', bins=10)

    with open(os.path.join(out_path, 'evaluation_report.json'), 'w') as f:
        json.dump({"uplift_at_30pct":uatk,"auuc_approx":auuc,"qini_curve_values":curve}, f, indent=2)
    print({"uplift_at_30pct":uatk,"auuc_approx":auuc})

if __name__ == "__main__":
    main()

    # "args": [
    #     "--features",
    #     "data/processed/features_user_week.csv",
    #     "--uplift",
    #     "artifacts/predictions/uplift_predictions.csv",
    #     "--out",
    #     "artifacts"
    #   ]
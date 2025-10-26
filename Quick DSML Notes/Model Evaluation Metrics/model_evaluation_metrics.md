# 📊 Model Evaluation Metrics

Machine learning metrics help us understand how good a model’s predictions are. They differ based on model task type.

# 🧠 Types of Model Evaluation Problems

| Problem Type                | What We Measure                        | Typical Metrics                                           |
| --------------------------- | -------------------------------------- | --------------------------------------------------------- |
| Classification              | Correctly identify classes             | Accuracy, Precision, Recall, F1, ROC-AUC, PR-AUC, LogLoss |
| Regression                  | Predict continuous numeric values      | MAE, MSE, RMSE, R², MAPE                                  |
| Ranking / Recommendation    | Correctly rank relevant items          | Precision@k, Recall@k, MAP, NDCG                          |
| Clustering                  | Meaningful separation into groups      | Silhouette Score, Davies–Bouldin, Calinski–Harabasz       |
| Probabilistic / Forecasting | Good uncertainty/probability estimates | Brier Score, Pinball Loss, CRPS                           |

# ✅ Classification Metrics

📌 Confusion Matrix (Foundation for all metrics)
| | Predicted Positive | Predicted Negative |
| - | - | - |
| Actual Positive |TP |FN|
| Actual Negative |FP |TN|

## 🟢 Accuracy

**Formula**: (TP + TN) / (TP + FP + TN + FN)

**Meaning**: Fraction of all correct predictions.

✅ Good when classes are balanced.

⚠️ Bad when classes are imbalanced (e.g., fraud detection).

**Memory trick**: “How accurate overall?”

## 🟣 Precision

**Formula**: TP / (TP + FP)

**Meaning**: Of all predicted positives, how many were actually positive.

✅ Good when false alarms are costly (e.g., banning legitimate users).

**Memory trick**: Precision → “How precise were your positive guesses?”

## 🔵 Recall (Sensitivity / True Positive Rate)

**Formula**: TP / (TP + FN)

**Meaning**: Of all actual positives, how many did you catch.

✅ Good when missing a positive is costly (e.g., missing fraud).

**Memory trick**: Recall → “How much did you recall from all real positives?”

## 🔶 F1-Score

**Formula**: 2 × (Precision × Recall) / (Precision + Recall)

**Meaning**: Harmonic mean of precision and recall.

✅ Good balance when both FP and FN matter.

**Memory trick**: F1 → “Fair 1-number trade-off.”

## 🟠 ROC-AUC (Receiver Operating Characteristic – Area Under Curve)

**Meaning**: Measures ranking ability — probability that a random positive is ranked higher than a random negative.

✅ Good overall discrimination metric.

**Memory trick**: ROC = “Ranking Of Classes.”

## 🟡 PR-AUC (Precision–Recall AUC)

**Meaning**: Focuses on the trade-off between precision and recall.

✅ Better than ROC-AUC for imbalanced data.

**Memory trick**: “PR-AUC zooms in on positive class performance.”

## 🔴 Log-Loss / Cross-Entropy

**Meaning**: Punishes confident wrong predictions heavily.

✅ Used when model outputs probabilities.

**Memory trick**: “Wrong and confident = logarithmically painful.”

# 📈 Regression Metrics

| Metric                          | Interpretation                | Memory Trick             |
| ------------------------------- | ----------------------------- | ------------------------ |
| MAE Mean Absolute Error         | Average absolute error        | “Simple average gap”     |
| MSE Mean Squared Error          | Penalizes large errors        | “Big mistakes hurt more” |
| RMSE Root MSE                   | Same unit as target           | “Real-world error size”  |
| R² Coefficient of Determination | % variance explained by model | “Closer to 1 = better”   |
| MAPE Percentage Error           | % error, intuitive            | “Percentage miss”        |

# 🧩 Ranking / Recommendation Metrics

| Metric                                       | Meaning                                                |
| -------------------------------------------- | ------------------------------------------------------ |
| Precision@k                                  | Of the top-k items recommended, how many are relevant. |
| Recall@k                                     | Of all relevant items, how many appear in top-k.       |
| MAP (Mean Average Precision)                 | Average precision over ranked results.                 |
| NDCG (Normalized Discounted Cumulative Gain) | Rewards correct ordering — higher rank = higher gain.  |

Memory trick:
“P@k cares about top-k quality, NDCG cares about top-k ordering.”

# 🌀 Clustering / Unsupervised Metrics

| Metric               | Meaning / Intuition                                                                            | Good When                      | Better Value |
| -------------------- | ---------------------------------------------------------------------------------------------- | ------------------------------ | ------------ |
| Silhouette Score     | Measures how similar an item is to its own cluster vs. others (−1 to 1). “1 = well-clustered.” | Distinct clusturs              | Higher       |
| Davies–Bouldin Index | Lower = better separation between clusters.                                                    | Smaller spread within clusters | Lower        |
| Calinski–Harabasz    | Higher = better defined clusters.                                                              | Better Separation              | Higher       |

# 🌤 Probabilistic & Forecasting Metrics

| Metric       | Meaning                                                                                    |
| ------------ | ------------------------------------------------------------------------------------------ |
| Brier Score  | Mean squared difference between predicted probabilities and actual outcomes (0 = perfect). |
| Pinball Loss | Used in quantile regression (forecasts).                                                   |
| CRPS         | Extends Brier to continuous distributions.                                                 |

# ✅ Quick Direction Guide

| Metric Type | Higher is Better                                     | Lower is Better                |
| ----------- | ---------------------------------------------------- | ------------------------------ |
| Success     | Accuracy, Precision, Recall, F1, AUC, R², Silhouette | —                              |
| Error       | —                                                    | MSE, RMSE, MAE, Logloss, Brier |

# 💡 How to Choose a Metric Quickly

| Scenario                          | Best Metric                   |
| --------------------------------- | ----------------------------- |
| Balanced Classification           | Accuracy                      |
| Imbalanced Classification (fraud) | Recall, Precision, F1, PR-AUC |
| Numeric Prediction                | RMSE + R²                     |
| Top-k Recommendations             | Precision@k / NDCG            |
| Clustering                        | Silhouette Score              |

# Bonus Summary table for Functions in metrics.py

| Function            | Task          | What it Evaluates                   |
| ------------------- | ------------- | ----------------------------------- |
| precision_at_k      | Ranking       | Quality of top-k predictions        |
| recall_at_k         | Ranking       | Coverage of relevant items          |
| average_precision   | Ranking       | Ranking quality of relevant items   |
| map_at_k            | Ranking       | Mean performance across users       |
| dcg_at_k            | Ranking       | Ordering discount (higher = better) |
| ndcg_at_k           | Ranking       | Normalized ideal rank (0–1)         |
| evaluate_clustering | Clustering    | Separation & density metrics        |
| brier_score         | Probabilistic | Probability accuracy                |
| mean_pinball_loss_q | Forecasting   | Quantile prediction accuracy        |
| as_pretty_dict      | Utility       | Pretty formatting                   |
| \_safe_round        | Utility       | Safe numeric rounding               |

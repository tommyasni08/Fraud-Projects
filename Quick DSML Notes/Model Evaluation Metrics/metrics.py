"""
metrics.py — Quick-Glance Model Evaluation Utilities
----------------------------------------------------
A compact, production-friendly set of helpers to compute common metrics
across Classification, Regression, Ranking/Recommendation, Clustering,
and Probabilistic/Forecasting tasks.

Dependencies:
  - numpy
  - scikit-learn (sklearn)
  - Optional: pandas (only for pretty-print convenience in examples)

Notes:
  - For classification, pass `y_proba` (positive-class probabilities) to get AUC/LogLoss (not based on final class labels (0 or 1), instead they judge how confident the model was about aech prediction).
  - For imbalanced data, PR-AUC is often more informative than ROC-AUC.
  - For ranking/recsys, see precision_at_k / recall_at_k / map_at_k / ndcg_at_k.
  - For probabilistic forecasting, see brier_score and mean_pinball_loss_q.
"""

import math
from typing import Dict, Iterable, List, Optional, Sequence, Tuple

import numpy as np

# --- Classification ---
from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    roc_auc_score,
    average_precision_score,   # PR-AUC
    log_loss,
    confusion_matrix,
)

# --- Regression ---
from sklearn.metrics import (
    mean_absolute_error,
    mean_squared_error,
    r2_score,
    mean_absolute_percentage_error,
)

# --- Clustering ---
try:
    from sklearn.metrics import (
        silhouette_score,
        davies_bouldin_score,
        calinski_harabasz_score,
    )
    _HAS_CLUSTER = True
except Exception:
    # If user has a very old sklearn, clustering metrics might be missing.
    _HAS_CLUSTER = False

# --- Probabilistic / Forecasting ---
from sklearn.metrics import (
    brier_score_loss,
    mean_pinball_loss,  # For quantile forecasts
)


# =========================
# Classification Utilities
# =========================

def evaluate_classification(
    y_true: Sequence[int],
    y_pred: Sequence[int],
    y_proba: Optional[Sequence[float]] = None,
    pos_label: int = 1,
    average: str = "binary",
) -> Dict[str, float]:
    """Compute common classification metrics.

    Args:
        y_true: Ground truth labels (0/1 for binary).
        y_pred: Predicted labels (0/1 for binary).
        y_proba: Optional positive-class probabilities (same length as y_true).
        pos_label: The label considered as positive class.
        average: 'binary' for binary classification; 'macro' or 'weighted' for multiclass.

    Returns:
        Dict with metrics. If `y_proba` provided, adds AUC/PR-AUC/LogLoss.
    """
    y_true = np.asarray(y_true)
    y_pred = np.asarray(y_pred)

    out = {
        "accuracy": accuracy_score(y_true, y_pred),
        "precision": precision_score(y_true, y_pred, pos_label=pos_label, average=average, zero_division=0),
        "recall": recall_score(y_true, y_pred, pos_label=pos_label, average=average, zero_division=0),
        "f1": f1_score(y_true, y_pred, pos_label=pos_label, average=average, zero_division=0),
    }

    if y_proba is not None:
        y_proba = np.asarray(y_proba)
        # For ROC-AUC / PR-AUC with multiclass, you'd need one-vs-rest handling.
        try:
            out["roc_auc"] = roc_auc_score(y_true, y_proba)
        except Exception:
            # Fallback if shapes/classes unexpected
            pass
        try:
            out["pr_auc"] = average_precision_score(y_true, y_proba)
        except Exception:
            pass
        try:
            out["log_loss"] = log_loss(y_true, np.vstack([1 - y_proba, y_proba]).T)
        except Exception:
            # If y_proba already shape (n,2) or multiclass, user should pass in proper proba matrix.
            try:
                out["log_loss"] = log_loss(y_true, y_proba)
            except Exception:
                pass

    # Confusion matrix (TP, FP, TN, FN) for quick glance
    cm = confusion_matrix(y_true, y_pred, labels=[pos_label, 1 - pos_label]) if set(np.unique(y_true)) <= {0,1} else confusion_matrix(y_true, y_pred)
    out["cm_TP"] = float(cm[0, 0]) if cm.ndim == 2 else float("nan")
    out["cm_FN"] = float(cm[0, 1]) if cm.ndim == 2 else float("nan")
    out["cm_FP"] = float(cm[1, 0]) if cm.ndim == 2 else float("nan")
    out["cm_TN"] = float(cm[1, 1]) if cm.ndim == 2 else float("nan")

    return out


# ====================
# Regression Utilities
# ====================

def evaluate_regression(
    y_true: Sequence[float],
    y_pred: Sequence[float],
) -> Dict[str, float]:
    """Compute common regression metrics.

    Returns:
        Dict with MAE, MSE, RMSE, R2, MAPE.
    """
    y_true = np.asarray(y_true, dtype=float)
    y_pred = np.asarray(y_pred, dtype=float)

    mae = mean_absolute_error(y_true, y_pred)
    mse = mean_squared_error(y_true, y_pred)
    rmse = float(np.sqrt(mse))
    r2 = r2_score(y_true, y_pred)
    # Handle zero targets safely for MAPE (sklearn will deal with it but may warn).
    mape = mean_absolute_percentage_error(y_true, y_pred)

    return {
        "mae": mae,
        "mse": mse,
        "rmse": rmse,
        "r2": r2,
        "mape": mape,
    }


# ================================
# Ranking / Recommendation Metrics
# ================================

def precision_at_k(y_true_rel: Sequence[int], y_score: Sequence[float], k: int) -> float: # Demo Purpose
    """Precision@k for a single ranked list.

    Args:
        y_true_rel: Binary relevance (1=relevant, 0=not).
        y_score: Scores used to rank (higher = more relevant).
        k: Cutoff.

    Returns:
        Precision@k in [0, 1].
    """
    order = np.argsort(-np.asarray(y_score))
    topk = np.asarray(y_true_rel)[order][:k]
    return float(np.mean(topk))


def recall_at_k(y_true_rel: Sequence[int], y_score: Sequence[float], k: int) -> float: # Demo Purpose
    """Recall@k for a single ranked list.

    Returns:
        Recall@k in [0, 1].
    """
    y_true_rel = np.asarray(y_true_rel)
    n_rel = int(np.sum(y_true_rel))
    if n_rel == 0:
        return 0.0
    order = np.argsort(-np.asarray(y_score))
    topk = y_true_rel[order][:k]
    return float(np.sum(topk) / n_rel)


def average_precision(y_true_rel: Sequence[int], y_score: Sequence[float]) -> float:
    """Average Precision for a single ranked list.

    Equivalent to area under Precision-Recall curve for that list.
    """
    # Sort by decreasing score
    y_true_rel = np.asarray(y_true_rel)
    order = np.argsort(-np.asarray(y_score))
    rel_sorted = y_true_rel[order]

    cum_rel = np.cumsum(rel_sorted)
    ranks = np.arange(1, len(rel_sorted) + 1)
    precision_at_i = cum_rel / ranks

    # Sum precision at ranks where item is relevant
    ap = float(np.sum(precision_at_i * rel_sorted) / max(1, np.sum(rel_sorted)))
    return ap


def map_at_k(list_of_y_true_rel: Sequence[Sequence[int]], list_of_y_score: Sequence[Sequence[float]], k: Optional[int] = None) -> float:
    """Mean Average Precision across multiple lists.

    If k is provided, compute AP on top-k truncated lists.
    """
    aps: List[float] = []
    for y_true_rel, y_score in zip(list_of_y_true_rel, list_of_y_score):
        y_true_rel = np.asarray(y_true_rel)
        y_score = np.asarray(y_score)
        if k is not None:
            order = np.argsort(-y_score)
            order = order[:k]
            aps.append(average_precision(y_true_rel[order], y_score[order]))
        else:
            aps.append(average_precision(y_true_rel, y_score))
    return float(np.mean(aps)) if aps else 0.0


def dcg_at_k(y_true_rel: Sequence[float], y_score: Sequence[float], k: int, gains: str = "exp2") -> float:
    """Discounted Cumulative Gain at k.

    Args:
        y_true_rel: Relevance grades (can be 0/1 or graded).
        y_score: Scores to rank by.
        k: Cutoff.
        gains: 'exp2' -> gain = 2^rel - 1 (default); 'linear' -> gain = rel.
    """
    order = np.argsort(-np.asarray(y_score))
    rel = np.asarray(y_true_rel)[order][:k]

    if gains == "exp2":
        gains_vec = (2.0 ** rel) - 1.0
    else:
        gains_vec = rel.astype(float)

    discounts = 1.0 / np.log2(np.arange(2, k + 2))
    return float(np.sum(gains_vec * discounts))


def ndcg_at_k(y_true_rel: Sequence[float], y_score: Sequence[float], k: int, gains: str = "exp2") -> float:
    """Normalized DCG at k (in [0, 1])."""
    ideal_order = np.argsort(-np.asarray(y_true_rel))
    ideal_rel = np.asarray(y_true_rel)[ideal_order][:k]
    ideal_dcg = dcg_at_k(ideal_rel, ideal_rel, k, gains=gains)  # score with ideal ranking
    if ideal_dcg == 0.0:
        return 0.0
    actual_dcg = dcg_at_k(y_true_rel, y_score, k, gains=gains)
    return float(actual_dcg / ideal_dcg)


# ====================
# Clustering Utilities
# ====================

def evaluate_clustering(X: np.ndarray, labels: Sequence[int]) -> Dict[str, float]:
    """Compute common clustering metrics.

    Returns:
        Dict with silhouette, davies_bouldin, calinski_harabasz where available.
    """
    if not _HAS_CLUSTER:
        raise ImportError(
            "Clustering metrics unavailable — please upgrade scikit-learn to a version that includes "
            "silhouette_score, davies_bouldin_score, and calinski_harabasz_score."
        )
    labels = np.asarray(labels)
    return {
        "silhouette": silhouette_score(X, labels),
        "davies_bouldin": davies_bouldin_score(X, labels),
        "calinski_harabasz": calinski_harabasz_score(X, labels),
    }


# =================================
# Probabilistic / Forecasting Utils
# =================================

def brier_score(y_true: Sequence[int], y_proba: Sequence[float]) -> float:
    """Brier score for binary outcomes (lower is better)."""
    return float(brier_score_loss(y_true, y_proba))


def mean_pinball_loss_q(y_true: Sequence[float], y_pred_quantile: Sequence[float], q: float) -> float:
    """Mean pinball (quantile) loss at quantile q in (0,1).

    Example:
        q = 0.9  # P90 forecast
        loss = mean_pinball_loss_q(y_true, y_pred_p90, q)
    """
    return float(mean_pinball_loss(y_true, y_pred_quantile, alpha=q))


# ======================
# Pretty Print Utilities
# ======================

def _safe_round(x, n=6):
    try:
        return round(float(x), n)
    except Exception:
        return x


def as_pretty_dict(d: Dict[str, float], ndigits: int = 6) -> Dict[str, float]:
    """Round floats for prettier printing/logging."""
    return {k: _safe_round(v, ndigits) for k, v in d.items()}


# ============
# Quick Demos
# ============

if __name__ == "__main__":
    # Mini sanity demos (replace with your tests)
    rng = np.random.default_rng(0)

    # --- Classification demo ---
    y_true_cls = rng.integers(0, 2, size=1000)
    y_proba_cls = rng.random(1000)
    y_pred_cls = (y_proba_cls >= 0.5).astype(int)
    cls_metrics = evaluate_classification(y_true_cls, y_pred_cls, y_proba_cls)
    print("[Classification]", as_pretty_dict(cls_metrics))

    # --- Regression demo ---
    y_true_reg = rng.normal(0, 1, size=500)
    y_pred_reg = y_true_reg + rng.normal(0, 0.5, size=500)
    reg_metrics = evaluate_regression(y_true_reg, y_pred_reg)
    print("[Regression]", as_pretty_dict(reg_metrics))

    # --- Ranking demo (single list) ---
    y_rel = rng.integers(0, 2, size=50)
    y_score = rng.random(50)
    print("[Ranking] P@10", _safe_round(precision_at_k(y_rel, y_score, 10)))
    print("[Ranking] R@10", _safe_round(recall_at_k(y_rel, y_score, 10)))
    print("[Ranking] AP   ", _safe_round(average_precision(y_rel, y_score)))
    print("[Ranking] NDCG@10", _safe_round(ndcg_at_k(y_rel, y_score, 10)))

    # --- Probabilistic demo ---
    print("[Prob] Brier", _safe_round(brier_score(y_true_cls, y_proba_cls)))
    print("[Prob] Pinball@0.9", _safe_round(mean_pinball_loss_q(y_true_reg, y_pred_reg, 0.9)))

    # --- Clustering demo (if available) ---
    if _HAS_CLUSTER:
        # Create toy blobs
        from sklearn.datasets import make_blobs
        X, labels = make_blobs(n_samples=400, centers=4, random_state=0, cluster_std=0.80)
        clu = evaluate_clustering(X, labels)
        print("[Clustering]", as_pretty_dict(clu))
    else:
        print("[Clustering] Skipped (metrics unavailable in current sklearn).")


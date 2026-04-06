"""RandomForest, XGBoost, and Isolation Forest — training and inference with safe labels."""

from __future__ import annotations

import logging
import warnings
from typing import Any

import numpy as np
from sklearn.ensemble import IsolationForest, RandomForestClassifier
from sklearn.preprocessing import LabelEncoder
from xgboost import XGBClassifier

logger = logging.getLogger(__name__)

FEATURE_NAMES = [
    "permissions_count",
    "has_admin_policy",
    "has_star_action",
    "trust_account_count",
    "cross_account",
    "age_days",
    "inline_policy_count",
    "managed_policy_count",
]

_rf: RandomForestClassifier | None = None
_xgb: XGBClassifier | None = None
_if: IsolationForest | None = None
_if_threshold: float = -0.1
_trained: bool = False
_level_encoder: LabelEncoder | None = None


def normalize_labels(y: np.ndarray) -> np.ndarray:
    """Map arbitrary class integers to contiguous 0..K-1 for sklearn / XGBoost."""
    le = LabelEncoder()
    return le.fit_transform(y.astype(int))


def _synthetic_dataset(n_samples: int = 500, seed: int = 42) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    rng = np.random.default_rng(seed)
    X = np.zeros((n_samples, len(FEATURE_NAMES)), dtype=np.float64)
    y_level = np.zeros(n_samples, dtype=np.int32)
    y_score = np.zeros(n_samples, dtype=np.float64)

    for i in range(n_samples):
        perms = int(rng.integers(0, 250))
        has_adm = int(rng.random() < 0.08)
        has_star = int(rng.random() < 0.12)
        trust = int(rng.integers(0, 8))
        cross = int(rng.random() < 0.15)
        age = int(rng.integers(1, 800))
        inline = int(rng.integers(0, 6))
        managed = int(rng.integers(0, 15))
        X[i] = [perms, has_adm, has_star, trust, cross, age, inline, managed]

        raw = (
            perms * 0.25
            + has_adm * 35
            + has_star * 25
            + trust * 3
            + cross * 15
            + min(age / 30.0, 20)
            + inline * 4
            + managed * 2
        )
        score_0_100 = int(np.clip(raw + rng.normal(0, 6), 0, 100))
        y_score[i] = score_0_100
        if score_0_100 >= 80:
            y_level[i] = 3
        elif score_0_100 >= 55:
            y_level[i] = 2
        elif score_0_100 >= 30:
            y_level[i] = 1
        else:
            y_level[i] = 0

    return X, y_level, y_score


def train_models() -> bool:
    """
    Train RF, XGBoost, and Isolation Forest.
    Returns True on success, False on failure (does not raise).
    """
    global _rf, _xgb, _if, _if_threshold, _trained, _level_encoder
    warnings.filterwarnings("ignore", category=UserWarning)

    try:
        X, y_level, y_score = _synthetic_dataset(500, seed=42)

        _level_encoder = LabelEncoder()
        y_level_enc = _level_encoder.fit_transform(y_level.astype(int))

        y_score_bins = np.clip((y_score / 25.0).astype(int), 0, 3)
        y_xgb_enc = normalize_labels(y_score_bins)
        num_class = int(len(np.unique(y_xgb_enc)))
        if num_class < 2:
            y_xgb_enc = np.concatenate([y_xgb_enc, np.array([1 - y_xgb_enc[0]])])
            X = np.vstack([X, X[0:1]])
            num_class = int(len(np.unique(y_xgb_enc)))

        _rf = RandomForestClassifier(
            n_estimators=120,
            max_depth=12,
            random_state=42,
            class_weight="balanced",
        )
        _rf.fit(X, y_level_enc)

        _xgb = XGBClassifier(
            n_estimators=80,
            max_depth=6,
            learning_rate=0.08,
            objective="multi:softprob",
            num_class=num_class,
            random_state=42,
            verbosity=0,
        )
        _xgb.fit(X, y_xgb_enc)

        _if = IsolationForest(
            n_estimators=200,
            contamination=0.1,
            random_state=42,
        )
        _if.fit(X)
        scores = _if.decision_function(X)
        _if_threshold = float(np.percentile(scores, 10))

        _trained = True
        logger.info("ML models trained: RF, XGBoost, IsolationForest (num_class=%s)", num_class)
        return True
    except Exception as e:
        logger.exception("ML training failed (app continues degraded): %s", e)
        _rf = None
        _xgb = None
        _if = None
        _trained = False
        _level_encoder = None
        return False


def _row_from_features(features: dict[str, Any]) -> np.ndarray:
    return np.array(
        [
            float(features.get("permissions_count", 0)),
            float(features.get("has_admin_policy", 0)),
            float(features.get("has_star_action", 0)),
            float(features.get("trust_account_count", 0)),
            float(features.get("cross_account", 0)),
            float(features.get("age_days", 0)),
            float(features.get("inline_policy_count", 0)),
            float(features.get("managed_policy_count", 0)),
        ],
        dtype=np.float64,
    ).reshape(1, -1)


def score_role(role_features: dict[str, Any]) -> dict[str, Any]:
    """Return risk_score, level, if_score, anomaly for one role feature dict."""
    if not _trained or _rf is None or _xgb is None or _if is None:
        train_models()
    if not _trained or _rf is None or _xgb is None or _if is None:
        return {
            "risk_score": 50,
            "level": "MEDIUM",
            "if_score": 0.0,
            "anomaly": False,
        }

    row = _row_from_features(role_features)
    level_map = {0: "LOW", 1: "MEDIUM", 2: "HIGH", 3: "CRITICAL"}
    rf_pred = _rf.predict(row)
    if _level_encoder is not None:
        try:
            orig = int(_level_encoder.inverse_transform(rf_pred)[0])
            level = level_map.get(orig, "MEDIUM")
        except (ValueError, IndexError, TypeError):
            level = level_map.get(int(rf_pred[0]), "MEDIUM")
    else:
        level = level_map.get(int(rf_pred[0]), "MEDIUM")

    proba = _xgb.predict_proba(row)[0]
    nc = len(proba)
    weights = np.linspace(20.0, 95.0, num=nc) if nc > 0 else np.array([50.0])
    risk_score = int(np.clip(float(np.sum(proba * weights)), 0, 100))

    if_score = float(_if.decision_function(row)[0])
    anomaly = bool(if_score < _if_threshold)

    return {
        "risk_score": risk_score,
        "level": level,
        "if_score": if_score,
        "anomaly": anomaly,
    }


def get_model_info() -> dict[str, Any]:
    if not _trained or _rf is None or _xgb is None or _if is None:
        return {
            "status": "not_trained",
            "random_forest": {},
            "xgboost": {},
            "isolation_forest": {},
        }
    imp = _rf.feature_importances_.tolist()
    importance = dict(zip(FEATURE_NAMES, imp, strict=False))
    ncls = len(_xgb.classes_) if hasattr(_xgb, "classes_") else 4
    return {
        "random_forest": {
            "n_estimators": _rf.n_estimators,
            "feature_importance": importance,
        },
        "xgboost": {
            "n_estimators": int(getattr(_xgb, "n_estimators", 80)),
            "objective": "multi:softprob",
            "num_class": int(ncls),
        },
        "isolation_forest": {
            "contamination": 0.1,
            "n_estimators": _if.n_estimators,
            "decision_threshold": _if_threshold,
        },
    }


def models_ready() -> bool:
    return bool(_trained and _rf is not None and _xgb is not None and _if is not None)

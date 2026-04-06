from pathlib import Path

import joblib
from sklearn.ensemble import IsolationForest, RandomForestClassifier

from .features import FEATURE_COLUMNS
from .synthetic_data import generate_synthetic_iam_data

MODELS_DIR = Path(__file__).resolve().parents[2] / "models"
ISO_PATH = MODELS_DIR / "isolation_forest.joblib"
RF_PATH = MODELS_DIR / "random_forest.joblib"


def train_models() -> None:
    MODELS_DIR.mkdir(parents=True, exist_ok=True)
    df = generate_synthetic_iam_data(10000)
    x = df[FEATURE_COLUMNS]
    y = df["high_risk"]
    iso = IsolationForest(contamination=0.1, random_state=42)
    iso.fit(x)
    rf = RandomForestClassifier(n_estimators=200, random_state=42)
    rf.fit(x, y)
    joblib.dump(iso, ISO_PATH)
    joblib.dump(rf, RF_PATH)


def ensure_models() -> None:
    if not ISO_PATH.exists() or not RF_PATH.exists():
        train_models()

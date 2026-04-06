from typing import Any, Dict, List

import joblib

from .features import FEATURE_COLUMNS, matrix_from_identities
from .train import ISO_PATH, RF_PATH, ensure_models


def score_identities(identities: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    ensure_models()
    iso = joblib.load(ISO_PATH)
    rf = joblib.load(RF_PATH)
    if not identities:
        return []
    x = matrix_from_identities(identities)
    anomaly_pred = iso.predict(x)
    prob = rf.predict_proba(x)
    importances = getattr(rf, "feature_importances_", [0.0] * len(FEATURE_COLUMNS))
    top_feats = sorted(
        list(zip(FEATURE_COLUMNS, importances)),
        key=lambda t: t[1],
        reverse=True,
    )[:3]
    top_factors = [f[0] for f in top_feats]
    out = []
    for idx, identity in enumerate(identities):
        risk = int(round(float(prob[idx][1]) * 100))
        out.append(
            {
                "identity_id": identity["id"],
                "identity_name": identity["name"],
                "cloud": identity["cloud"],
                "type": identity["type"],
                "risk_score": risk,
                "anomaly_flag": anomaly_pred[idx] == -1,
                "top_risk_factors": top_factors,
            }
        )
    return out


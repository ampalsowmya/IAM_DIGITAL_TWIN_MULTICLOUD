from typing import Dict

import numpy as np
import pandas as pd


def generate_synthetic_iam_data(n: int = 10000) -> pd.DataFrame:
    rng = np.random.default_rng(42)
    df = pd.DataFrame(
        {
            "num_permissions": rng.integers(1, 300, n),
            "has_admin_action": rng.integers(0, 2, n),
            "cross_cloud_access": rng.integers(0, 2, n),
            "last_used_days": rng.integers(0, 365, n),
            "num_attached_policies": rng.integers(0, 25, n),
            "is_service_account": rng.integers(0, 2, n),
            "privilege_level": rng.integers(0, 11, n),
        }
    )
    anomaly = (
        (df["num_permissions"] > 220)
        | (df["has_admin_action"] == 1)
        | (df["privilege_level"] > 8)
    ).astype(int)
    high_risk = (
        (df["anomaly"] if "anomaly" in df else anomaly)
        | (df["cross_cloud_access"] & (df["num_attached_policies"] > 10))
        | (df["last_used_days"] > 250)
    ).astype(int)
    df["anomaly"] = anomaly
    df["high_risk"] = high_risk
    return df


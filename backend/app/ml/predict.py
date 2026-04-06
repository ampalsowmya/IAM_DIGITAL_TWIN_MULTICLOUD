"""
ML Risk Prediction Module
==========================
Uses trained ML models to predict IAM risk scores.

Risk Score: 0-100 scale
- 0-30: Low risk
- 31-70: Medium risk
- 71-100: High risk

Models used:
- RandomForest (default, more explainable)
- XGBoost (optional, higher accuracy)
"""
import logging
import os
from typing import Dict, Any, Optional, List, Any as _AnyType

import numpy as np

from .features import extract_features, extract_feature_matrix
from .train import (
    load_model,
    RANDOM_FOREST_MODEL_PATH,
    XGBOOST_MODEL_PATH,
    train_all_models,
)

logger = logging.getLogger(__name__)


def _load_or_retrain_model(path: str, cloud: Optional[str]) -> _AnyType:
    """
    Load a model from disk, retraining (and deleting old files) if incompatible.
    """
    try:
        return load_model(path)
    except Exception as exc:
        logger.warning(f"Failed to load model at {path}: {exc}. Retraining models.")
        # Delete incompatible model file if it exists.
        try:
            if os.path.exists(path):
                os.remove(path)
                logger.info(f"Removed incompatible model file: {path}")
        except Exception as remove_exc:
            logger.warning(f"Failed to remove model file {path}: {remove_exc}")
        # Retrain all models sequentially.
        train_all_models(cloud=cloud)
        # Attempt to load again after retraining.
        return load_model(path)


def calculate_risk_score(
    role_name: str,
    cloud: Optional[str] = None,
    model_type: str = "random_forest"
) -> Dict[str, Any]:
    """
    Calculate risk score for a specific role.
    
    Args:
        role_name: Role name to score
        cloud: Optional cloud filter
        model_type: "random_forest" or "xgboost"
        
    Returns:
        Dictionary with risk score and explainable factors
    """
    # Extract features for this role
    all_features = extract_features(cloud=cloud)
    role_features = [f for f in all_features if f["role"] == role_name]
    
    if not role_features:
        logger.warning(f"Role {role_name} not found in graph")
        return {
            "role": role_name,
            "cloud": cloud,
            "risk_score": 0,
            "risk_level": "unknown",
            "error": "Role not found"
        }
    
    feature_dict = role_features[0]
    feature_matrix = extract_feature_matrix([feature_dict])

    if feature_matrix is None or len(feature_matrix) == 0:
        raise ValueError("Feature matrix is empty. Cannot calculate risk score.")
    
    # Load and use model
    try:
        if model_type == "xgboost" and os.path.exists(XGBOOST_MODEL_PATH):
            model = _load_or_retrain_model(XGBOOST_MODEL_PATH, cloud=cloud)
        else:
            model = _load_or_retrain_model(RANDOM_FOREST_MODEL_PATH, cloud=cloud)
        
        # Predict risk (0-1 scale)
        risk_probability = model.predict(feature_matrix)[0]
        
        # Convert to 0-100 scale
        risk_score = int(risk_probability * 100)
        risk_score = max(0, min(100, risk_score))  # Clamp to 0-100
        
        # Determine risk level
        if risk_score <= 30:
            risk_level = "low"
        elif risk_score <= 70:
            risk_level = "medium"
        else:
            risk_level = "high"
        
        # Extract explainable factors
        explainable_factors = _extract_explainable_factors(feature_dict, model, feature_matrix)
        
        return {
            "role": role_name,
            "cloud": feature_dict["cloud"],
            "risk_score": risk_score,
            "risk_level": risk_level,
            "risk_probability": round(risk_probability, 4),
            "explainable_factors": explainable_factors,
            "model_type": model_type
        }
        
    except FileNotFoundError:
        logger.warning("ML model not found. Train models first using train.py")
        # Fallback: simple heuristic-based scoring
        return _heuristic_risk_score(feature_dict)


def _extract_explainable_factors(
    feature_dict: Dict[str, Any],
    model,
    feature_matrix: np.ndarray
) -> Dict[str, Any]:
    """
    Extract explainable factors contributing to risk score.
    
    Uses feature importance from the model to explain why a role is risky.
    
    Args:
        feature_dict: Feature dictionary for the role
        model: Trained ML model
        feature_matrix: Feature matrix for the role
        
    Returns:
        Dictionary with explainable factors
    """
    # Get feature importances
    if hasattr(model, "feature_importances_"):
        importances = model.feature_importances_
        feature_names = [
            "policy_count", "dangerous_perm_count", "wildcard_perm_count",
            "total_permissions", "permission_diversity", "cloud_risk_weight",
            "has_assume_role", "has_pass_role", "hierarchy_depth"
        ]
        
        # Get top contributing factors
        top_factors = sorted(
            zip(feature_names, importances, feature_matrix[0]),
            key=lambda x: x[1],
            reverse=True
        )[:5]
        
        factors = {}
        for name, importance, value in top_factors:
            factors[name] = {
                "importance": round(float(importance), 4),
                "value": round(float(value), 4),
                "contribution": round(float(importance * value), 4)
            }
        
        return {
            "top_contributing_factors": factors,
            "primary_risk_indicators": [
                name for name, _, _ in top_factors[:3]
            ]
        }
    else:
        return {"note": "Model does not support feature importance"}


def _heuristic_risk_score(feature_dict: Dict[str, Any]) -> Dict[str, Any]:
    """
    Fallback heuristic risk scoring when ML model is not available.
    
    Args:
        feature_dict: Feature dictionary
        
    Returns:
        Risk score dictionary
    """
    dangerous_count = feature_dict.get("dangerous_perm_count", 0)
    wildcard_count = feature_dict.get("wildcard_perm_count", 0)
    total_perms = feature_dict.get("total_permissions", 0)
    policy_count = feature_dict.get("policy_count", 0)
    
    # Simple heuristic
    risk_score = min(100, (
        dangerous_count * 30 +
        wildcard_count * 25 +
        min(total_perms / 10, 20) +
        min(policy_count * 2, 25)
    ))
    
    if risk_score <= 30:
        risk_level = "low"
    elif risk_score <= 70:
        risk_level = "medium"
    else:
        risk_level = "high"
    
    return {
        "role": feature_dict["role"],
        "cloud": feature_dict["cloud"],
        "risk_score": int(risk_score),
        "risk_level": risk_level,
        "method": "heuristic",
        "explainable_factors": {
            "dangerous_permissions": dangerous_count,
            "wildcard_permissions": wildcard_count,
            "total_permissions": total_perms,
            "policy_count": policy_count
        }
    }


def batch_calculate_risk_scores(
    role_names: Optional[List[str]] = None,
    cloud: Optional[str] = None,
    model_type: str = "random_forest"
) -> List[Dict[str, Any]]:
    """
    Calculate risk scores for multiple roles.
    
    Args:
        role_names: Optional list of specific roles (None = all roles)
        cloud: Optional cloud filter
        model_type: Model to use
        
    Returns:
        List of risk score dictionaries
    """
    all_features = extract_features(cloud=cloud)
    
    if role_names:
        all_features = [f for f in all_features if f["role"] in role_names]
    
    results = []
    for feature_dict in all_features:
        try:
            score = calculate_risk_score(
                feature_dict["role"],
                cloud=feature_dict["cloud"],
                model_type=model_type
            )
            results.append(score)
        except Exception as e:
            logger.error(f"Failed to calculate risk for {feature_dict['role']}: {e}")
            continue
    
    # Sort by risk score (highest first)
    results.sort(key=lambda x: x.get("risk_score", 0), reverse=True)
    
    return results


if __name__ == "__main__":
    import logging
    logging.basicConfig(level=logging.INFO)
    
    print("\n=== RISK SCORE PREDICTION ===")
    
    # Calculate scores for all roles
    scores = batch_calculate_risk_scores()
    
    print(f"\nCalculated risk scores for {len(scores)} roles")
    print("\nTop 10 Riskiest Roles:")
    for i, score in enumerate(scores[:10], 1):
        print(f"{i}. {score['role']} ({score['cloud']}): "
              f"Risk={score['risk_score']}/100 ({score['risk_level']})")

"""
ML Risk Prediction Module
==========================
Uses trained ML models to predict IAM risk scores.

Risk Score: 0-100 scale
- 0-30: Low risk
- 31-70: Medium risk
- 71-100: High risk

Models used:
- RandomForest (default, more explainable)
- XGBoost (optional, higher accuracy)
"""
import logging
import os
from typing import Dict, Any, Optional, List
import numpy as np
from .features import extract_features, extract_feature_matrix
from .train import load_model, RANDOM_FOREST_MODEL_PATH, XGBOOST_MODEL_PATH

logger = logging.getLogger(__name__)


def calculate_risk_score(
    role_name: str,
    cloud: Optional[str] = None,
    model_type: str = "random_forest"
) -> Dict[str, Any]:
    """
    Calculate risk score for a specific role.
    
    Args:
        role_name: Role name to score
        cloud: Optional cloud filter
        model_type: "random_forest" or "xgboost"
        
    Returns:
        Dictionary with risk score and explainable factors
    """
    # Extract features for this role
    all_features = extract_features(cloud=cloud)
    role_features = [f for f in all_features if f["role"] == role_name]
    
    if not role_features:
        logger.warning(f"Role {role_name} not found in graph")
        return {
            "role": role_name,
            "cloud": cloud,
            "risk_score": 0,
            "risk_level": "unknown",
            "error": "Role not found"
        }
    
    feature_dict = role_features[0]
    feature_matrix = extract_feature_matrix([feature_dict])
    
    # Load and use model
    try:
        if model_type == "xgboost" and os.path.exists(XGBOOST_MODEL_PATH):
            model = load_model(XGBOOST_MODEL_PATH)
        else:
            model = load_model(RANDOM_FOREST_MODEL_PATH)
        
        # Predict risk (0-1 scale)
        risk_probability = model.predict(feature_matrix)[0]
        
        # Convert to 0-100 scale
        risk_score = int(risk_probability * 100)
        risk_score = max(0, min(100, risk_score))  # Clamp to 0-100
        
        # Determine risk level
        if risk_score <= 30:
            risk_level = "low"
        elif risk_score <= 70:
            risk_level = "medium"
        else:
            risk_level = "high"
        
        # Extract explainable factors
        explainable_factors = _extract_explainable_factors(feature_dict, model, feature_matrix)
        
        return {
            "role": role_name,
            "cloud": feature_dict["cloud"],
            "risk_score": risk_score,
            "risk_level": risk_level,
            "risk_probability": round(risk_probability, 4),
            "explainable_factors": explainable_factors,
            "model_type": model_type
        }
        
    except FileNotFoundError:
        logger.warning("ML model not found. Train models first using train.py")
        # Fallback: simple heuristic-based scoring
        return _heuristic_risk_score(feature_dict)


def _extract_explainable_factors(
    feature_dict: Dict[str, Any],
    model,
    feature_matrix: np.ndarray
) -> Dict[str, Any]:
    """
    Extract explainable factors contributing to risk score.
    
    Uses feature importance from the model to explain why a role is risky.
    
    Args:
        feature_dict: Feature dictionary for the role
        model: Trained ML model
        feature_matrix: Feature matrix for the role
        
    Returns:
        Dictionary with explainable factors
    """
    # Get feature importances
    if hasattr(model, "feature_importances_"):
        importances = model.feature_importances_
        feature_names = [
            "policy_count", "dangerous_perm_count", "wildcard_perm_count",
            "total_permissions", "permission_diversity", "cloud_risk_weight",
            "has_assume_role", "has_pass_role", "hierarchy_depth"
        ]
        
        # Get top contributing factors
        top_factors = sorted(
            zip(feature_names, importances, feature_matrix[0]),
            key=lambda x: x[1],
            reverse=True
        )[:5]
        
        factors = {}
        for name, importance, value in top_factors:
            factors[name] = {
                "importance": round(float(importance), 4),
                "value": round(float(value), 4),
                "contribution": round(float(importance * value), 4)
            }
        
        return {
            "top_contributing_factors": factors,
            "primary_risk_indicators": [
                name for name, _, _ in top_factors[:3]
            ]
        }
    else:
        return {"note": "Model does not support feature importance"}


def _heuristic_risk_score(feature_dict: Dict[str, Any]) -> Dict[str, Any]:
    """
    Fallback heuristic risk scoring when ML model is not available.
    
    Args:
        feature_dict: Feature dictionary
        
    Returns:
        Risk score dictionary
    """
    dangerous_count = feature_dict.get("dangerous_perm_count", 0)
    wildcard_count = feature_dict.get("wildcard_perm_count", 0)
    total_perms = feature_dict.get("total_permissions", 0)
    policy_count = feature_dict.get("policy_count", 0)
    
    # Simple heuristic
    risk_score = min(100, (
        dangerous_count * 30 +
        wildcard_count * 25 +
        min(total_perms / 10, 20) +
        min(policy_count * 2, 25)
    ))
    
    if risk_score <= 30:
        risk_level = "low"
    elif risk_score <= 70:
        risk_level = "medium"
    else:
        risk_level = "high"
    
    return {
        "role": feature_dict["role"],
        "cloud": feature_dict["cloud"],
        "risk_score": int(risk_score),
        "risk_level": risk_level,
        "method": "heuristic",
        "explainable_factors": {
            "dangerous_permissions": dangerous_count,
            "wildcard_permissions": wildcard_count,
            "total_permissions": total_perms,
            "policy_count": policy_count
        }
    }


def batch_calculate_risk_scores(
    role_names: Optional[List[str]] = None,
    cloud: Optional[str] = None,
    model_type: str = "random_forest"
) -> List[Dict[str, Any]]:
    """
    Calculate risk scores for multiple roles.
    
    Args:
        role_names: Optional list of specific roles (None = all roles)
        cloud: Optional cloud filter
        model_type: Model to use
        
    Returns:
        List of risk score dictionaries
    """
    all_features = extract_features(cloud=cloud)
    
    if role_names:
        all_features = [f for f in all_features if f["role"] in role_names]
    
    results = []
    for feature_dict in all_features:
        try:
            score = calculate_risk_score(
                feature_dict["role"],
                cloud=feature_dict["cloud"],
                model_type=model_type
            )
            results.append(score)
        except Exception as e:
            logger.error(f"Failed to calculate risk for {feature_dict['role']}: {e}")
            continue
    
    # Sort by risk score (highest first)
    results.sort(key=lambda x: x.get("risk_score", 0), reverse=True)
    
    return results


if __name__ == "__main__":
    import logging
    logging.basicConfig(level=logging.INFO)
    
    print("\n=== RISK SCORE PREDICTION ===")
    
    # Calculate scores for all roles
    scores = batch_calculate_risk_scores()
    
    print(f"\nCalculated risk scores for {len(scores)} roles")
    print("\nTop 10 Riskiest Roles:")
    for i, score in enumerate(scores[:10], 1):
        print(f"{i}. {score['role']} ({score['cloud']}): "
              f"Risk={score['risk_score']}/100 ({score['risk_level']})")

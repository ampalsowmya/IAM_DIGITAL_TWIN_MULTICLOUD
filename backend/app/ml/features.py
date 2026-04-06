from typing import Any, Dict, List


FEATURE_COLUMNS = [
    "num_permissions",
    "has_admin_action",
    "cross_cloud_access",
    "last_used_days",
    "num_attached_policies",
    "is_service_account",
    "privilege_level",
]


def extract_features_from_identity(identity: Dict[str, Any]) -> Dict[str, float]:
    permissions = identity.get("permissions", [])
    actions = [p.get("action", "") for p in permissions]
    return {
        "num_permissions": float(len(permissions)),
        "has_admin_action": float(any("admin" in a.lower() or a == "*" for a in actions)),
        "cross_cloud_access": float(identity.get("cross_cloud_access", 0)),
        "last_used_days": float(identity.get("last_used_days", 30)),
        "num_attached_policies": float(identity.get("num_attached_policies", max(1, len(permissions) // 8))),
        "is_service_account": float(identity.get("type") in {"service_account", "app", "role"}),
        "privilege_level": float(identity.get("privilege_level", min(10, len(permissions) // 15))),
    }


def matrix_from_identities(identities: List[Dict[str, Any]]) -> List[List[float]]:
    rows: List[List[float]] = []
    for i in identities:
        f = extract_features_from_identity(i)
        rows.append([f[c] for c in FEATURE_COLUMNS])
    return rows

"""
ML Feature Extraction Module
============================
Extracts graph-based features for ML risk scoring.

Features extracted:
1. Policy count per role
2. Dangerous permission count
3. Wildcard privilege detection
4. Role hierarchy depth
5. Cloud-specific privilege weight
6. Permission diversity
7. Escalation path length
"""
import logging
from typing import List, Dict, Any, Optional

import numpy as np

from ..graph.neo4j_client import Neo4jClient
from ..graph.escalation import AWS_ESCALATION_PERMISSIONS, is_wildcard_permission
from ..config import settings

logger = logging.getLogger(__name__)

# In AWS-only mode, all dangerous permissions are AWS permissions.
ALL_DANGEROUS_PERMISSIONS = AWS_ESCALATION_PERMISSIONS


def extract_features(cloud: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Extract ML-ready features from the IAM graph.
    Each role becomes one training sample with multiple features.
    
    Features:
    - policy_count: Number of policies attached to role
    - dangerous_perm_count: Count of escalation-risk permissions
    - wildcard_perm_count: Count of wildcard permissions
    - total_permissions: Total unique permissions
    - permission_diversity: Ratio of unique permissions to total
    - cloud_risk_weight: Cloud-specific risk multiplier
    - has_assume_role: Boolean for assume role capability
    - has_pass_role: Boolean for pass role capability
    
    Args:
        cloud: Optional cloud filter
        
    Returns:
        List of feature dictionaries, one per role
    """
    client = Neo4jClient()

    effective_cloud = (cloud or settings.default_cloud or "aws").lower()

    query = """
    MATCH (r:Role {cloud: $cloud})
    OPTIONAL MATCH (r)-[:HAS_POLICY]->(p:Policy)
    OPTIONAL MATCH (p)-[:HAS_PERMISSION]->(perm:Permission)
    WITH r, p, perm
    RETURN
        r.name AS role,
        r.cloud AS cloud,
        count(DISTINCT p) AS policy_count,
        collect(DISTINCT perm.name) AS permissions
    """
    
    features = []
    
    try:
        with client.driver.session() as session:
            result = session.run(query, cloud=effective_cloud)
            
            for row in result:
                role = row["role"]
                role_cloud = row["cloud"] or "unknown"
                permissions = row["permissions"] or []
                policy_count = row["policy_count"] or 0
                
                # Calculate feature values
                dangerous_perms = set(permissions) & set(ALL_DANGEROUS_PERMISSIONS)
                dangerous_count = len(dangerous_perms)
                
                wildcard_perms = [p for p in permissions if is_wildcard_permission(p)]
                wildcard_count = len(wildcard_perms)
                
                total_permissions = len(permissions)
                
                # Permission diversity: unique permissions / (policies * avg_perms_per_policy)
                # Higher diversity = more complex permission structure
                permission_diversity = (
                    total_permissions / (policy_count * 10) if policy_count > 0 else 0
                )
                
                # Cloud-specific risk weight (AWS-only mode)
                cloud_risk_weight = {
                    "aws": 1.0,
                    "unknown": 0.5,
                }.get(role_cloud, 0.5)
                
                # Specific dangerous permission flags
                has_assume_role = any("AssumeRole" in p for p in permissions)
                has_pass_role = any("PassRole" in p for p in permissions)
                
                # Calculate role hierarchy depth (simplified)
                # In a real implementation, this would traverse role assumption chains
                hierarchy_depth = 1  # Default depth
                
                features.append({
                    "role": role,
                    "cloud": role_cloud,
                    "policy_count": policy_count,
                    "dangerous_perm_count": dangerous_count,
                    "wildcard_perm_count": wildcard_count,
                    "total_permissions": total_permissions,
                    "permission_diversity": round(permission_diversity, 4),
                    "cloud_risk_weight": cloud_risk_weight,
                    "has_assume_role": 1 if has_assume_role else 0,
                    "has_pass_role": 1 if has_pass_role else 0,
                    "hierarchy_depth": hierarchy_depth,
                })
        
        logger.info(f"Extracted features for {len(features)} roles")
        return features
        
    finally:
        client.close()


def extract_feature_matrix(features: List[Dict[str, Any]]) -> np.ndarray:
    """
    Convert feature dictionaries to numpy matrix for ML training.
    
    Feature order:
    1. policy_count
    2. dangerous_perm_count
    3. wildcard_perm_count
    4. total_permissions
    5. permission_diversity
    6. cloud_risk_weight
    7. has_assume_role
    8. has_pass_role
    9. hierarchy_depth
    
    Args:
        features: List of feature dictionaries
        
    Returns:
        Numpy array of shape (n_samples, n_features)
    """
    feature_order = [
        "policy_count",
        "dangerous_perm_count",
        "wildcard_perm_count",
        "total_permissions",
        "permission_diversity",
        "cloud_risk_weight",
        "has_assume_role",
        "has_pass_role",
        "hierarchy_depth"
    ]
    
    matrix = []
    for feat in features:
        row = [feat.get(key, 0) for key in feature_order]
        matrix.append(row)
    
    return np.array(matrix)


def generate_synthetic_labels(features: List[Dict[str, Any]]) -> np.ndarray:
    """
    Generate synthetic risk labels for training.
    
    Label generation logic:
    - High risk (1): dangerous_perm_count > 0 OR wildcard_perm_count > 0
    - Medium risk (0.5): total_permissions > 50 OR policy_count > 10
    - Low risk (0): otherwise
    
    In production, labels would come from:
    - Historical security incidents
    - Manual security reviews
    - External threat intelligence
    
    Args:
        features: List of feature dictionaries
        
    Returns:
        Numpy array of risk labels (0-1 scale)
    """
    labels = []
    
    for feat in features:
        dangerous_count = feat.get("dangerous_perm_count", 0)
        wildcard_count = feat.get("wildcard_perm_count", 0)
        total_perms = feat.get("total_permissions", 0)
        policy_count = feat.get("policy_count", 0)
        
        # Risk scoring logic
        if dangerous_count > 0 or wildcard_count > 0:
            risk_score = 1.0  # High risk
        elif total_perms > 50 or policy_count > 10:
            risk_score = 0.5  # Medium risk
        else:
            risk_score = 0.0  # Low risk
        
        # Apply cloud risk weight
        risk_score *= feat.get("cloud_risk_weight", 1.0)
        risk_score = min(risk_score, 1.0)  # Cap at 1.0
        
        labels.append(risk_score)
    
    return np.array(labels)


if __name__ == "__main__":
    import logging
    logging.basicConfig(level=logging.INFO)
    
    print("\n=== FEATURE EXTRACTION ===")
    features = extract_features()
    
    print(f"\nExtracted {len(features)} role features")
    if features:
        print("\nSample features:")
        for feat in features[:3]:
            print(f"  {feat['role']} ({feat['cloud']}): "
                  f"policies={feat['policy_count']}, "
                  f"dangerous={feat['dangerous_perm_count']}, "
                  f"wildcards={feat['wildcard_perm_count']}")


import logging
from typing import Any, Dict, List

logger = logging.getLogger(__name__)

def ingest_gcp_iam() -> List[Dict[str, Any]]:
    """Fetch GCP IAM entities if credentials exist, otherwise return empty."""
    try:
        from google.cloud import iam_admin_v1
        from google.auth import default
    except Exception:  # noqa: BLE001
        logger.warning("google-cloud libraries unavailable; returning empty GCP result.")
        return []

    try:
        _, project = default()
        if not project:
            logger.warning("GCP credentials/project not found; returning empty.")
            return []
        client = iam_admin_v1.IAMClient()
        entities: List[Dict[str, Any]] = []
        parent = f"projects/{project}"
        for sa in client.list_service_accounts(request={"name": parent}):
            entities.append(
                {
                    "id": sa.unique_id,
                    "name": sa.display_name or sa.email,
                    "cloud": "gcp",
                    "type": "role",
                    "permissions": [
                        {
                            "action": "gcp:serviceAccount",
                            "resource": sa.name,
                            "effect": "Allow",
                            "condition": {},
                        }
                    ],
                    "tags": [],
                    "email": sa.email,
                }
            )
        return entities
    except Exception as exc:  # noqa: BLE001
        logger.warning("GCP IAM ingestion skipped: %s", exc)
        return []

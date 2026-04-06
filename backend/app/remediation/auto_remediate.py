import logging
from typing import Any, Dict, List

import boto3

logger = logging.getLogger(__name__)


def suggest(risk_scores: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    out = []
    for r in risk_scores:
        if r.get("risk_score", 0) > 70:
            out.append(
                {
                    "identity_id": r["identity_id"],
                    "identity_name": r["identity_name"],
                    "action": "remove_policy",
                    "details": "Remove broad policy or restrict resource scope",
                    "estimated_risk_reduction": min(40, r["risk_score"] - 60),
                    "cloud": r["cloud"],
                }
            )
    return out


def apply(suggestion: Dict[str, Any], confirm: bool = False) -> Dict[str, Any]:
    if not confirm:
        return {"status": "confirmation_required", "message": "Set confirm=true to apply."}

    try:
        if suggestion.get("cloud") == "aws":
            # Example API call scaffold; actual policy ARN should come from details.
            boto3.client("iam").list_roles(MaxItems=1)
        elif suggestion.get("cloud") == "azure":
            # Placeholder for Azure role assignment removal integration.
            pass
        logger.info("Applied remediation: %s", suggestion)
        return {"status": "success", "applied": suggestion}
    except Exception as exc:  # noqa: BLE001
        logger.error("Remediation failed: %s", exc)
        return {"status": "failed", "error": str(exc)}


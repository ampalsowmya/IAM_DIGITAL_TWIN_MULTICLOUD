import json
import logging
from typing import Any, Dict

import boto3

from ..config import settings

logger = logging.getLogger(__name__)


def invoke_bedrock(prompt: str) -> str:
    """Invoke Bedrock Claude with graceful fallback."""
    try:
        client = boto3.client("bedrock-runtime", region_name=settings.AWS_REGION)
        body = json.dumps(
            {
                "anthropic_version": "bedrock-2023-05-31",
                "max_tokens": 500,
                "messages": [{"role": "user", "content": prompt}],
            }
        )
        response = client.invoke_model(modelId=settings.BEDROCK_MODEL_ID, body=body)
        payload: Dict[str, Any] = json.loads(response["body"].read())
        return payload["content"][0]["text"]
    except Exception as exc:  # noqa: BLE001
        logger.warning("Bedrock unavailable: %s", exc)
        return "Governance assistant unavailable right now. Showing fallback guidance."


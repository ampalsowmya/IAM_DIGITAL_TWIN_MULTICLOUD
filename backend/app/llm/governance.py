from typing import Any, Dict

from .bedrock import invoke_bedrock
from .prompts import COMPLIANCE_GAP_PROMPT, POLICY_RECOMMEND_PROMPT, RISK_EXPLAIN_PROMPT


def explain_risk(identity: Dict[str, Any]) -> Dict[str, Any]:
    prompt = RISK_EXPLAIN_PROMPT.format(
        name=identity.get("identity_name", identity.get("name")),
        score=identity.get("risk_score", 0),
        perms=identity.get("top_risk_factors", []),
    )
    return {"response": invoke_bedrock(prompt)}


def recommend_policy(identity: Dict[str, Any]) -> Dict[str, Any]:
    prompt = POLICY_RECOMMEND_PROMPT.format(perms=identity.get("permissions", []))
    return {"response": invoke_bedrock(prompt)}


def compliance_gaps(framework: str, summary: Dict[str, Any]) -> Dict[str, Any]:
    prompt = COMPLIANCE_GAP_PROMPT.format(framework=framework, summary=summary)
    return {"response": invoke_bedrock(prompt)}

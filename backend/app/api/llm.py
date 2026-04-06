from fastapi import APIRouter, Depends
from pydantic import BaseModel

from ..llm.governance import compliance_gaps, explain_risk, recommend_policy
from .deps import get_current_user

router = APIRouter(prefix="/governance", tags=["governance"])


class IdentityPayload(BaseModel):
    identity: dict


class CompliancePayload(BaseModel):
    framework: str
    summary: dict


@router.post("/explain")
async def explain(payload: IdentityPayload, user=Depends(get_current_user)):
    """
    Explain IAM risk in plain language.
    Example: {"response":"- ..."}
    """
    return explain_risk(payload.identity)


@router.post("/recommend")
async def recommend(payload: IdentityPayload, user=Depends(get_current_user)):
    """
    Recommend least-privilege policy.
    Example: {"response":"{...policy json...}"}
    """
    return recommend_policy(payload.identity)


@router.post("/compliance-gaps")
async def gaps(payload: CompliancePayload, user=Depends(get_current_user)):
    return compliance_gaps(payload.framework, payload.summary)


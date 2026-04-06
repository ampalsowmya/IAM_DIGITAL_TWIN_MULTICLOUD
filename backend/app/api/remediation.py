from fastapi import APIRouter, Depends
from pydantic import BaseModel

from ..remediation.auto_remediate import apply, suggest
from ..ml.score import score_identities
from ..api.risk import _load_identities
from .deps import get_current_user, require_role

router = APIRouter(prefix="/remediation", tags=["remediation"])


class ApplyRequest(BaseModel):
    suggestion: dict
    confirm: bool = False


@router.get("/suggestions")
async def suggestions(user=Depends(get_current_user)):
    """
    Get auto-remediation suggestions.
    Example: [{"identity_id":"...","action":"remove_policy"}]
    """
    scores = score_identities(await _load_identities())
    return suggest(scores)


@router.post("/apply")
async def apply_suggestion(req: ApplyRequest, user=Depends(require_role("analyst"))):
    """
    Apply one remediation item.
    Example: {"status":"success","applied":{...}}
    """
    return apply(req.suggestion, confirm=req.confirm)


from fastapi import APIRouter, Depends

from ..compliance.frameworks import FRAMEWORKS
from ..compliance.report import generate_compliance_report
from ..ml.score import score_identities
from ..api.risk import _load_identities
from .deps import get_current_user

router = APIRouter(prefix="/compliance", tags=["compliance"])


@router.get("/report")
async def report(framework: str = "ISO 27001", user=Depends(get_current_user)):
    """
    Get compliance report by framework.
    Example: {"framework":"ISO 27001","controls":[...]}
    """
    scores = score_identities(await _load_identities())
    return generate_compliance_report(framework, scores)


@router.get("/gaps")
async def gaps(user=Depends(get_current_user)):
    """
    Get framework list and quick control counts.
    Example: {"ISO 27001":3, "NIST CSF":7, "SOC2":3}
    """
    return {k: len(v) for k, v in FRAMEWORKS.items()}


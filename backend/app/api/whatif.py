from typing import List, Literal

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from ..graph.neo4j_client import get_neo4j_client
from ..graph.whatif import simulate_what_if
from .deps import get_current_user

router = APIRouter(prefix="/whatif", tags=["whatif"])


class Change(BaseModel):
    type: Literal["add", "remove"]
    permission: str
    resource: str = "*"


class WhatIfRequest(BaseModel):
    identity_id: str
    proposed_changes: List[Change]


@router.post("/simulate")
async def simulate(req: WhatIfRequest, user=Depends(get_current_user)):
    """
    Run what-if IAM risk simulation.
    Example: {"current_risk":40,"projected_risk":75,"risk_delta":35}
    """
    return await simulate_what_if(
        get_neo4j_client(), req.identity_id, [c.dict() for c in req.proposed_changes]
    )


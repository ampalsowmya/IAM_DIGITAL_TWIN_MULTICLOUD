from fastapi import APIRouter, Depends, HTTPException

from ..ml.score import score_identities
from ..graph.neo4j_client import get_neo4j_client
from .deps import get_current_user

router = APIRouter(prefix="/risk", tags=["risk"])


async def _load_identities():
    rows = await get_neo4j_client().run_query(
        "MATCH (i:Identity)-[:HAS_ROLE]->(r:Role) OPTIONAL MATCH (r)-[:GRANTS]->(p:Permission) RETURN i.id as id, i.name as name, i.cloud as cloud, i.identity_type as type, collect({action:p.action,resource:p.resource,effect:p.effect}) as permissions"
    )
    return rows


@router.get("/scores")
async def get_risk_scores(user=Depends(get_current_user)):
    """
    Get risk scores for all identities.
    Example: [{"identity_id":"...","risk_score":82}]
    """
    return score_identities(await _load_identities())


@router.get("/score/{identity_id}")
async def get_risk_score(identity_id: str, user=Depends(get_current_user)):
    """
    Get risk score for one identity.
    Example: {"identity_id":"123","risk_score":40}
    """
    scores = score_identities(await _load_identities())
    for s in scores:
        if s["identity_id"] == identity_id:
            return s
    raise HTTPException(status_code=404, detail="Identity not found")


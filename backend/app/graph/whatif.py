from typing import Any, Dict, List

from .escalation import detect_escalation_paths
from .neo4j_client import AsyncNeo4jClient


def _permission_risk(permission: str) -> int:
    if permission == "*":
        return 30
    if "admin" in permission.lower():
        return 20
    if permission.endswith(":*"):
        return 15
    return 3


async def simulate_what_if(
    client: AsyncNeo4jClient, identity_id: str, proposed_changes: List[Dict[str, Any]]
) -> Dict[str, Any]:
    rows = await client.run_query(
        """
        MATCH (i:Identity {id:$id})-[:HAS_ROLE]->(r:Role)-[:GRANTS]->(p:Permission)
        RETURN collect(p.action) AS actions
        """,
        {"id": identity_id},
    )
    current_actions = set(rows[0]["actions"] if rows else [])
    projected = set(current_actions)
    for c in proposed_changes:
        if c["type"] == "add":
            projected.add(c["permission"])
        if c["type"] == "remove":
            projected.discard(c["permission"])

    current_risk = min(100, sum(_permission_risk(a) for a in current_actions))
    projected_risk = min(100, sum(_permission_risk(a) for a in projected))
    escalation = await detect_escalation_paths(client)
    return {
        "current_risk": current_risk,
        "projected_risk": projected_risk,
        "risk_delta": projected_risk - current_risk,
        "new_escalation_paths": escalation[:5] if projected_risk >= current_risk else [],
        "removed_escalation_paths": escalation[:5] if projected_risk < current_risk else [],
    }


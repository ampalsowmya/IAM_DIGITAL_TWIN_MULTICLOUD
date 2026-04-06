from typing import Any, Dict, List

from .neo4j_client import AsyncNeo4jClient


ESCALATION_QUERY = """
MATCH path = (i:Identity)-[:HAS_ROLE|GRANTS|CROSS_CLOUD_LINKED*1..5]->(p:Permission)
WHERE toLower(coalesce(p.action,'')) CONTAINS 'admin'
   OR p.action IN ['iam:PassRole', 'sts:AssumeRole', '*', 'azure:role_assignment']
WITH i, path, length(path) AS path_length
RETURN i.id AS source_id,
       i.name AS source_name,
       nodes(path) AS path_nodes,
       path_length,
       CASE
         WHEN path_length <= 2 THEN 'CRITICAL'
         WHEN path_length <= 4 THEN 'HIGH'
         ELSE 'MEDIUM'
       END AS risk_level,
       i.cloud AS cloud
ORDER BY path_length ASC
LIMIT 100
"""


async def detect_escalation_paths(client: AsyncNeo4jClient) -> List[Dict[str, Any]]:
    rows = await client.run_query(ESCALATION_QUERY)
    out: List[Dict[str, Any]] = []
    for r in rows:
        nodes = [
            {"id": n.get("id"), "name": n.get("name"), "label": list(n.labels)[0]}
            for n in r["path_nodes"]
        ]
        out.append(
            {
                "path": nodes,
                "risk_level": r["risk_level"],
                "cloud": r["cloud"],
                "source_identity": r["source_name"],
                "path_length": r["path_length"],
                "target_privilege": nodes[-1]["name"] if nodes else "unknown",
            }
        )
    return out

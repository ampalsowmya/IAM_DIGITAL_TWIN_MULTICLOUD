from typing import Any, Dict, List

from .neo4j_client import AsyncNeo4jClient


async def ingest_entities(client: AsyncNeo4jClient, entities: List[Dict[str, Any]]) -> None:
    for e in entities:
        await client.run_write_query(
            """
            MERGE (i:Identity {id:$id})
            SET i.name=$name, i.cloud=$cloud, i.identity_type=$type
            """,
            {"id": e["id"], "name": e["name"], "cloud": e["cloud"], "type": e["type"]},
        )
        role_id = f"{e['cloud']}:{e['name']}"
        await client.run_write_query(
            """
            MERGE (r:Role {id:$rid})
            SET r.name=$name, r.cloud=$cloud
            MERGE (i:Identity {id:$iid})
            MERGE (i)-[:HAS_ROLE]->(r)
            """,
            {"rid": role_id, "name": e["name"], "cloud": e["cloud"], "iid": e["id"]},
        )
        for idx, perm in enumerate(e.get("permissions", [])):
            pid = f"{role_id}:perm:{idx}:{perm.get('action')}"
            await client.run_write_query(
                """
                MERGE (p:Permission {id:$pid})
                SET p.action=$action, p.resource=$resource, p.effect=$effect
                WITH p
                MATCH (r:Role {id:$rid})
                MERGE (r)-[:GRANTS {permission_type:$action}]->(p)
                """,
                {
                    "pid": pid,
                    "rid": role_id,
                    "action": perm.get("action", "unknown"),
                    "resource": perm.get("resource", "*"),
                    "effect": perm.get("effect", "Allow"),
                },
            )

    await client.run_write_query(
        """
        MATCH (a:Identity), (b:Identity)
        WHERE a.id <> b.id AND a.email IS NOT NULL AND b.email IS NOT NULL
          AND toLower(a.email) = toLower(b.email)
        MERGE (a)-[:CROSS_CLOUD_LINKED]->(b)
        """
    )


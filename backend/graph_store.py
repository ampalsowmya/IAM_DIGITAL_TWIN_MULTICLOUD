"""Neo4j graph storage, connectivity wait, and API routes."""

from __future__ import annotations

import asyncio
import logging
from typing import Any

from fastapi import APIRouter, Depends
from neo4j import Driver, GraphDatabase

from auth import CurrentUser
from models import EscalationPath, GraphEdge, GraphNode, GraphResponse

logger = logging.getLogger(__name__)

_driver: Driver | None = None


async def wait_for_neo4j(driver: Driver, retries: int = 10, delay: float = 3.0) -> bool:
    """Wait until Neo4j accepts connections (sync driver wrapped with asyncio.to_thread)."""
    for attempt in range(1, retries + 1):
        try:
            await asyncio.to_thread(driver.verify_connectivity)
            logger.info("Neo4j connectivity verified")
            return True
        except Exception as e:
            logger.warning("Neo4j not ready (%s/%s): %s", attempt, retries, e)
            if attempt < retries:
                await asyncio.sleep(delay)
    raise RuntimeError("Neo4j not ready after %s attempts" % retries)


def get_driver() -> Driver:
    global _driver
    if _driver is None:
        raise RuntimeError("Neo4j driver not initialized")
    return _driver


def init_driver(uri: str, user: str, password: str) -> Driver:
    global _driver
    _driver = GraphDatabase.driver(uri, auth=(user, password))
    return _driver


def close_driver() -> None:
    global _driver
    if _driver is not None:
        _driver.close()
        _driver = None


def init_schema(session: Any) -> None:
    session.run(
        "CREATE CONSTRAINT iam_role_id IF NOT EXISTS FOR (r:IAMRole) REQUIRE r.id IS UNIQUE"
    )
    session.run(
        "CREATE CONSTRAINT policy_id IF NOT EXISTS FOR (p:Policy) REQUIRE p.id IS UNIQUE"
    )


def create_role_node(tx, role_data: dict[str, Any]) -> None:
    tx.run(
        """
        MERGE (r:IAMRole {id: $id})
        SET r.name = $name,
            r.cloud = $cloud,
            r.create_date = $create_date,
            r.permissions_count = $permissions_count,
            r.has_admin_policy = $has_admin_policy,
            r.has_star_action = $has_star_action,
            r.trust_account_count = $trust_account_count,
            r.cross_account = $cross_account,
            r.age_days = $age_days,
            r.inline_policy_count = $inline_policy_count,
            r.managed_policy_count = $managed_policy_count,
            r.assume_policy_json = $assume_policy_json
        """,
        id=role_data["id"],
        name=role_data["name"],
        cloud=role_data.get("cloud", "aws"),
        create_date=role_data.get("create_date", ""),
        permissions_count=int(role_data.get("permissions_count", 0)),
        has_admin_policy=int(role_data.get("has_admin_policy", 0)),
        has_star_action=int(role_data.get("has_star_action", 0)),
        trust_account_count=int(role_data.get("trust_account_count", 0)),
        cross_account=int(role_data.get("cross_account", 0)),
        age_days=int(role_data.get("age_days", 0)),
        inline_policy_count=int(role_data.get("inline_policy_count", 0)),
        managed_policy_count=int(role_data.get("managed_policy_count", 0)),
        assume_policy_json=role_data.get("assume_policy_json", ""),
    )


def create_policy_node(tx, policy_data: dict[str, Any]) -> None:
    tx.run(
        """
        MERGE (p:Policy {id: $id})
        SET p.name = $name,
            p.cloud = $cloud
        """,
        id=policy_data["id"],
        name=policy_data.get("name", ""),
        cloud=policy_data.get("cloud", "aws"),
    )


def create_relationship(tx, from_id: str, to_id: str, rel_type: str) -> None:
    if rel_type == "CAN_ASSUME":
        tx.run(
            """
            MATCH (a:IAMRole {id: $from_id})
            MATCH (b:IAMRole {id: $to_id})
            MERGE (a)-[:CAN_ASSUME]->(b)
            """,
            from_id=from_id,
            to_id=to_id,
        )
    elif rel_type == "HAS_POLICY":
        tx.run(
            """
            MATCH (a:IAMRole {id: $from_id})
            MATCH (p:Policy {id: $to_id})
            MERGE (a)-[:HAS_POLICY]->(p)
            """,
            from_id=from_id,
            to_id=to_id,
        )


def clear_cloud_nodes(session: Any, cloud: str) -> None:
    session.run(
        """
        MATCH (n)
        WHERE (n:IAMRole OR n:Policy) AND n.cloud = $cloud
        DETACH DELETE n
        """,
        cloud=cloud,
    )


def _write_ingestion(tx, payload: dict[str, Any]) -> int:
    roles = payload.get("roles", [])
    policies = payload.get("policies", [])
    rels = payload.get("relationships", [])
    for r in roles:
        create_role_node(tx, r)
    for p in policies:
        create_policy_node(tx, p)
    for rel in rels:
        create_relationship(tx, rel["from_id"], rel["to_id"], rel["type"])
    return len(rels)


def store_ingestion_batch(session: Any, payload: dict[str, Any]) -> int:
    """Persist roles, policies, and edges. Returns relationship count created."""
    return session.execute_write(_write_ingestion, payload)


router = APIRouter(prefix="/graph", tags=["graph"])


@router.get("", response_model=GraphResponse)
async def get_graph(_: CurrentUser):
    driver = get_driver()
    nodes: list[GraphNode] = []
    edges: list[GraphEdge] = []
    with driver.session() as session:
        result = session.run(
            """
            MATCH (n)
            WHERE n:IAMRole OR n:Policy
            RETURN labels(n) AS labs, properties(n) AS props
            """
        )
        for rec in result:
            props = dict(rec["props"])
            node_id = str(props.get("id", ""))
            name = props.get("name", node_id)
            ntype = "IAMRole" if "IAMRole" in rec["labs"] else "Policy"
            cloud = props.get("cloud", "aws")
            rs = float(props.get("risk_score", 0.0)) if "risk_score" in props else 0.0
            nodes.append(
                GraphNode(
                    id=node_id,
                    name=name,
                    type=ntype,
                    risk_score=rs,
                    cloud=cloud,
                )
            )
        er = session.run(
            """
            MATCH (a)-[r]->(b)
            WHERE (a:IAMRole OR a:Policy) AND (b:IAMRole OR b:Policy)
            RETURN a.id AS src, b.id AS tgt, type(r) AS rt
            """
        )
        for rec in er:
            edges.append(
                GraphEdge(
                    source=rec["src"],
                    target=rec["tgt"],
                    relationship=rec["rt"],
                )
            )
    return GraphResponse(nodes=nodes, edges=edges)


@router.get("/escalation-paths", response_model=list[EscalationPath])
async def get_escalation_paths(_: CurrentUser):
    driver = get_driver()
    paths: list[EscalationPath] = []
    with driver.session() as session:
        result = session.run(
            """
            MATCH p = (r1:IAMRole)-[:CAN_ASSUME*1..3]->(r2:IAMRole)
            WHERE r1.id <> r2.id
            WITH p, nodes(p) AS ns
            RETURN [x IN ns | coalesce(x.name, x.id)] AS names,
                   ns[0].id AS r1id,
                   ns[size(ns)-1].id AS r2id
            LIMIT 500
            """
        )
        for rec in result:
            names = rec["names"]
            r1 = rec["r1id"]
            r2 = rec["r2id"]
            if not names:
                continue
            paths.append(
                EscalationPath(
                    from_role=r1,
                    to_role=r2,
                    path=list(names),
                    risk_level="HIGH",
                )
            )
    return paths

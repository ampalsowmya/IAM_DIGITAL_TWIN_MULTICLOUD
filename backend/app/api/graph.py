from fastapi import APIRouter, Depends

from ..graph.escalation import detect_escalation_paths
from ..graph.neo4j_client import get_neo4j_client
from .deps import get_current_user

router = APIRouter(prefix="/graph", tags=["graph"])


@router.get("")
async def get_graph(user=Depends(get_current_user)):
    """
    Return graph nodes and edges.

    Example response:
    {"nodes":[...], "edges":[...]}
    """
    client = get_neo4j_client()
    nodes = await client.run_query("MATCH (n) RETURN id(n) AS nid, labels(n) AS labels, properties(n) AS props LIMIT 500")
    edges = await client.run_query(
        "MATCH (a)-[r]->(b) RETURN id(a) AS source, id(b) AS target, type(r) AS label, properties(r) AS props LIMIT 1000"
    )
    return {"nodes": nodes, "edges": edges}


@router.get("/escalation-paths")
async def get_escalation_paths(user=Depends(get_current_user)):
    """
    Return detected escalation paths.

    Example response:
    [{"source_identity":"alice","risk_level":"HIGH","path":[...]}]
    """
    return await detect_escalation_paths(get_neo4j_client())


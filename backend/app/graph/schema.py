from .neo4j_client import AsyncNeo4jClient


SCHEMA_QUERIES = [
    "CREATE CONSTRAINT identity_id_unique IF NOT EXISTS FOR (i:Identity) REQUIRE i.id IS UNIQUE",
    "CREATE CONSTRAINT policy_id_unique IF NOT EXISTS FOR (p:Policy) REQUIRE p.id IS UNIQUE",
    "CREATE INDEX identity_cloud_idx IF NOT EXISTS FOR (i:Identity) ON (i.cloud)",
    "CREATE INDEX identity_risk_idx IF NOT EXISTS FOR (i:Identity) ON (i.risk_score)",
    "CREATE INDEX identity_type_idx IF NOT EXISTS FOR (i:Identity) ON (i.identity_type)",
]


async def ensure_schema(client: AsyncNeo4jClient) -> None:
    for query in SCHEMA_QUERIES:
        await client.run_write_query(query)


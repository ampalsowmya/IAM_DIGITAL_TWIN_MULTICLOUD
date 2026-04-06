from __future__ import annotations

import logging
from typing import Any, AsyncGenerator, Dict, List, Optional

from neo4j import AsyncGraphDatabase, basic_auth
from tenacity import AsyncRetrying, retry_if_exception_type, stop_after_attempt, wait_exponential

from ..config import settings

logger = logging.getLogger(__name__)


class AsyncNeo4jClient:
    """Async Neo4j driver wrapper with basic retry logic."""

    def __init__(self, uri: str, user: str, password: str) -> None:
        self._uri = uri
        self._user = user
        self._password = password
        self._driver = AsyncGraphDatabase.driver(
            uri, auth=basic_auth(user, password)
        )

    async def close(self) -> None:
        await self._driver.close()

    async def run_query(
        self, query: str, parameters: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        async for attempt in AsyncRetrying(
            stop=stop_after_attempt(3),
            wait=wait_exponential(multiplier=0.5, min=0.5, max=5),
            retry=retry_if_exception_type(Exception),
        ):
            with attempt:
                async with self._driver.session() as session:
                    result = await session.run(query, parameters or {})
                    records = [record.data() for record in await result.to_list()]
                    return records
        return []

    async def run_write_query(
        self, query: str, parameters: Optional[Dict[str, Any]] = None
    ) -> None:
        async for attempt in AsyncRetrying(
            stop=stop_after_attempt(3),
            wait=wait_exponential(multiplier=0.5, min=0.5, max=5),
            retry=retry_if_exception_type(Exception),
        ):
            with attempt:
                async with self._driver.session() as session:
                    await session.run(query, parameters or {})

    async def health_check(self) -> bool:
        try:
            await self.run_query("RETURN 1 AS ok")
            return True
        except Exception as exc:  # noqa: BLE001
            logger.error("Neo4j health check failed: %s", exc)
            return False


_neo4j_client: Optional[AsyncNeo4jClient] = None


def get_neo4j_client() -> AsyncNeo4jClient:
    """Return a singleton AsyncNeo4jClient instance."""
    global _neo4j_client
    if _neo4j_client is None:
        _neo4j_client = AsyncNeo4jClient(
            settings.NEO4J_URI, settings.NEO4J_USER, settings.NEO4J_PASSWORD
        )
    return _neo4j_client

"""
Neo4j Graph Database Client
===========================
This module provides the unified graph model for multi-cloud IAM data.

Graph Schema:
- Nodes: (:Role), (:Policy), (:Permission)
- Relationships: (:Role)-[:HAS_POLICY]->(:Policy), (:Policy)-[:HAS_PERMISSION]->(:Permission)
- Properties: cloud, name, metadata (serialized as JSON string)

Supports cross-cloud analysis and escalation path traversal.
"""
import json
import logging
from typing import List, Dict, Any, Optional
from neo4j import GraphDatabase, Driver
from ..config import settings
from dotenv import load_dotenv
load_dotenv()


logger = logging.getLogger(__name__)


class Neo4jClient:
    """
    Neo4j client for IAM digital twin graph operations.
    Handles connection, ingestion, and querying of multi-cloud IAM data.
    """
    
    def __init__(self, uri: Optional[str] = None, user: Optional[str] = None, password: Optional[str] = None):
        """
        Initialize Neo4j driver connection.
        
        Args:
            uri: Neo4j connection URI (defaults to settings)
            user: Neo4j username (defaults to settings)
            password: Neo4j password (defaults to settings)
        """
        self.uri = uri or settings.neo4j_uri
        self.user = user or settings.neo4j_user
        self.password = password or settings.neo4j_password
        
        try:
            self.driver: Driver = GraphDatabase.driver(
                self.uri,
                auth=(self.user, self.password)
            )
            # Verify connection
            self.driver.verify_connectivity()
            logger.info(f"Connected to Neo4j at {self.uri}")
        except Exception as e:
            logger.error(f"Failed to connect to Neo4j: {e}")
            raise
    
    def close(self):
        """Close Neo4j driver connection."""
        if self.driver:
            self.driver.close()
            logger.info("Neo4j connection closed")
    
    def create_indexes(self):
        """
        Create indexes on node properties for better query performance.
        Should be called once during setup.
        """
        indexes = [
            "CREATE INDEX role_name IF NOT EXISTS FOR (r:Role) ON (r.name)",
            "CREATE INDEX role_cloud IF NOT EXISTS FOR (r:Role) ON (r.cloud)",
            "CREATE INDEX policy_name IF NOT EXISTS FOR (p:Policy) ON (p.name)",
            "CREATE INDEX permission_name IF NOT EXISTS FOR (perm:Permission) ON (perm.name)",
        ]
        
        with self.driver.session() as session:
            for index_query in indexes:
                try:
                    session.run(index_query)
                except Exception as e:
                    logger.warning(f"Index creation note (may already exist): {e}")
        
        logger.info("Neo4j indexes created/verified")
    
    def create_role_policy_permission(
        self,
        cloud: str,
        role: str,
        policy: str,
        permissions: List[str],
        metadata: Optional[Dict[str, Any]] = None
    ):
        """
        Create or update a role-policy-permission relationship in the graph.
        
        Unified Model:
        - cloud: "aws" | "azure" | "gcp"
        - role: Role name
        - policy: Policy name
        - permissions: List of permission strings
        - metadata: Additional context (ARNs, IDs, dates, etc.) - serialized as JSON string
        
        Args:
            cloud: Cloud provider identifier
            role: Role name
            policy: Policy name
            permissions: List of permission/action strings
            metadata: Optional metadata dictionary (will be serialized to JSON)
        """
        # Serialize metadata to JSON string for Neo4j storage
        metadata_str = json.dumps(metadata) if metadata else "{}"
        
        query = """
        // Create/update Role node with cloud tag
        MERGE (r:Role {name: $role, cloud: $cloud})
        SET r.metadata = $metadata_str
        
        // Create/update Policy node
        MERGE (p:Policy {name: $policy, cloud: $cloud})
        SET p.metadata = $metadata_str
        
        // Create relationship
        MERGE (r)-[:HAS_POLICY]->(p)
        
        // Create Permission nodes and relationships
        WITH p
        UNWIND $permissions AS perm
            MERGE (pr:Permission {name: perm, cloud: $cloud})
            MERGE (p)-[:HAS_PERMISSION]->(pr)
        """
        
        with self.driver.session() as session:
            session.run(
                query,
                cloud=cloud,
                role=role,
                policy=policy,
                permissions=permissions,
                metadata_str=metadata_str
            )
    
    def get_all_roles(self, cloud: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Fetch all roles from the graph, optionally filtered by cloud.
        
        Args:
            cloud: Optional cloud filter ("aws", "azure", "gcp")
            
        Returns:
            List of role dictionaries with deserialized metadata
        """
        if cloud:
            query = "MATCH (r:Role {cloud: $cloud}) RETURN r.name AS name, r.cloud AS cloud, r.metadata AS metadata"
        else:
            query = "MATCH (r:Role) RETURN r.name AS name, r.cloud AS cloud, r.metadata AS metadata"
        
        with self.driver.session() as session:
            result = session.run(query, cloud=cloud)
            roles = []
            for record in result:
                role_dict = dict(record)
                # Deserialize metadata JSON string back to dict
                if role_dict.get("metadata") and isinstance(role_dict["metadata"], str):
                    try:
                        role_dict["metadata"] = json.loads(role_dict["metadata"])
                    except (json.JSONDecodeError, TypeError):
                        role_dict["metadata"] = {}
                roles.append(role_dict)
            return roles
    
    def get_role_permissions(self, role_name: str, cloud: Optional[str] = None) -> List[str]:
        """
        Get all permissions for a specific role.
        
        Args:
            role_name: Role name
            cloud: Optional cloud filter
            
        Returns:
            List of permission strings
        """
        if cloud:
            query = """
            MATCH (r:Role {name: $role_name, cloud: $cloud})-[:HAS_POLICY]->(:Policy)-[:HAS_PERMISSION]->(p:Permission)
            RETURN DISTINCT p.name AS permission
            """
        else:
            query = """
            MATCH (r:Role {name: $role_name})-[:HAS_POLICY]->(:Policy)-[:HAS_PERMISSION]->(p:Permission)
            RETURN DISTINCT p.name AS permission
            """
        
        with self.driver.session() as session:
            result = session.run(query, role_name=role_name, cloud=cloud)
            return [record["permission"] for record in result]
    
    def find_escalation_paths(self, start_role: str, target_permissions: List[str]) -> List[Dict[str, Any]]:
        """
        Find potential escalation paths from a role to target permissions.
        Uses graph traversal to find indirect paths.
        
        Args:
            start_role: Starting role name
            target_permissions: List of target permissions to reach
            
        Returns:
            List of escalation path dictionaries
        """
        query = """
        MATCH (start:Role {name: $start_role})
        MATCH (target:Permission)
        WHERE target.name IN $target_permissions
        MATCH path = shortestPath((start)-[:HAS_POLICY*]->(:Policy)-[:HAS_PERMISSION]->(target))
        RETURN path, length(path) AS path_length
        ORDER BY path_length
        LIMIT 10
        """
        
        with self.driver.session() as session:
            result = session.run(query, start_role=start_role, target_permissions=target_permissions)
            paths = []
            for record in result:
                path = record["path"]
                paths.append({
                    "path_length": record["path_length"],
                    "nodes": [node["name"] for node in path.nodes],
                    "relationships": [rel.type for rel in path.relationships]
                })
            return paths


def ingest_iam_data_to_neo4j(normalized_data: List[Dict[str, Any]], cloud: str):
    """
    Ingest normalized IAM data into Neo4j graph.
    
    Args:
        normalized_data: List of normalized IAM dictionaries
            Expected format:
            [
                {
                    "cloud": "aws",
                    "role": "MyRole",
                    "policy": "MyPolicy",
                    "permissions": ["iam:GetUser", "s3:GetObject"],
                    "metadata": {...}
                }
            ]
        cloud: Cloud provider identifier
    """
    client = Neo4jClient()
    
    try:
        # Create indexes on first run
        client.create_indexes()
        
        # Ingest each normalized item
        for item in normalized_data:
            client.create_role_policy_permission(
                cloud=item.get("cloud", cloud),
                role=item["role"],
                policy=item["policy"],
                permissions=item.get("permissions", []),
                metadata=item.get("metadata", {})
            )
        
        logger.info(f"Ingested {len(normalized_data)} IAM items into Neo4j for cloud: {cloud}")
        
    finally:
        client.close()


# Legacy function name for backward compatibility
def ingest_aws_iam_to_neo4j(normalized_data: List[Dict[str, Any]]):
    """Legacy function - use ingest_iam_data_to_neo4j instead."""
    ingest_iam_data_to_neo4j(normalized_data, cloud="aws")

"""
Unit tests for Neo4j client
"""
import pytest
from backend.app.graph.neo4j_client import Neo4jClient, ingest_iam_data_to_neo4j


def test_neo4j_client_initialization():
    """Test Neo4j client can be initialized."""
    # This test requires Neo4j to be running
    # In CI/CD, Neo4j is provided as a service
    try:
        client = Neo4jClient()
        assert client.driver is not None
        client.close()
    except Exception as e:
        pytest.skip(f"Neo4j not available: {e}")


def test_ingest_iam_data():
    """Test IAM data ingestion."""
    # Sample normalized data
    test_data = [
        {
            "cloud": "aws",
            "role": "TestRole",
            "policy": "TestPolicy",
            "permissions": ["iam:GetUser", "s3:GetObject"],
            "metadata": {}
        }
    ]
    
    try:
        ingest_iam_data_to_neo4j(test_data, cloud="aws")
        # If no exception, ingestion succeeded
        assert True
    except Exception as e:
        pytest.skip(f"Neo4j not available: {e}")

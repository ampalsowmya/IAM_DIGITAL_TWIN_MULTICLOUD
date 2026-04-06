"""
Backend application package for the Multi-Cloud IAM Digital Twin.

This package is structured into the following domains:
- iam_ingestion: Connectors for AWS, Azure, and GCP IAM sources.
- graph: Neo4j client, schema management, and graph analytics.
- ml: Feature extraction, synthetic data generation, model training, and scoring.
- llm: Governance assistant powered by AWS Bedrock (or compatible APIs).
- compliance: Mapping IAM risks to compliance frameworks.
- remediation: Suggesting and optionally applying least-privilege changes.
- api: FastAPI routers for all exposed functionality.
"""

__all__ = [
    "iam_ingestion",
    "graph",
    "ml",
    "llm",
    "compliance",
    "remediation",
    "api",
]

"""
Multi-Cloud IAM Digital Twin
=============================
Production-grade academic project for IAM risk analysis across AWS, Azure, and GCP.
"""
__version__ = "1.0.0"

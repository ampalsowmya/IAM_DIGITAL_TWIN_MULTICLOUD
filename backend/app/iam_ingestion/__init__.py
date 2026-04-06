from .aws import ingest_aws_iam
from .azure import ingest_azure_iam
from .gcp import ingest_gcp_iam

__all__ = ["ingest_aws_iam", "ingest_azure_iam", "ingest_gcp_iam"]

"""
IAM Ingestion Module
====================
Multi-cloud IAM data ingestion from AWS, Azure AD, and GCP.
"""
from .aws import run_aws_iam_ingestion
from .azure import run_azure_ad_ingestion
from .gcp import run_gcp_iam_ingestion

__all__ = [
    "run_aws_iam_ingestion",
    "run_azure_ad_ingestion",
    "run_gcp_iam_ingestion"
]

from functools import lru_cache
from typing import Optional

from pydantic import BaseSettings, AnyUrl, validator


class Settings(BaseSettings):
    """Application configuration loaded from environment variables (.env in dev)."""

    # Neo4j
    NEO4J_URI: str
    NEO4J_USER: str = "neo4j"
    NEO4J_PASSWORD: str

    # AWS
    AWS_REGION: str = "us-east-1"
    AWS_ACCESS_KEY_ID: Optional[str] = None
    AWS_SECRET_ACCESS_KEY: Optional[str] = None

    # Azure
    AZURE_TENANT_ID: Optional[str] = None
    AZURE_CLIENT_ID: Optional[str] = None
    AZURE_CLIENT_SECRET: Optional[str] = None

    # Bedrock / LLM
    BEDROCK_MODEL_ID: str = "claude-sonnet-4-20250514"

    # Auth / JWT
    JWT_SECRET: str = "changeme"
    JWT_EXPIRE_MINUTES: int = 60

    # Misc
    ENVIRONMENT: str = "development"

    class Config:
        env_file = ".env"
        case_sensitive = False

    @validator("NEO4J_URI")
    def validate_neo4j_uri(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError(
                "NEO4J_URI is required and cannot be empty. "
                "Set it in your environment or .env file (e.g. bolt://neo4j:7687)."
            )
        if not (v.startswith("bolt://") or v.startswith("neo4j://")):
            raise ValueError(
                "NEO4J_URI must start with 'bolt://' or 'neo4j://', got: "
                f"{v!r}"
            )
        return v


@lru_cache()
def get_settings() -> Settings:
    """Return cached application settings instance."""

    return Settings()


settings = get_settings()

"""
Configuration management for Multi-Cloud IAM Digital Twin.
Loads environment variables from .env files for local development.
"""
import os
from typing import Optional

from dotenv import load_dotenv, find_dotenv
from pydantic_settings import BaseSettings
from pydantic import Field

from dotenv import load_dotenv
import os

load_dotenv()

# Load environment variables from .env files.
# This will pick up:
# - backend/.env           (when running from project root)
# - .env                   (when running inside backend/)
_root_env = find_dotenv()
if _root_env:
    load_dotenv(_root_env)

_backend_env = os.path.join(os.path.dirname(__file__), "..", ".env")
if os.path.exists(_backend_env):
    load_dotenv(_backend_env, override=False)


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Default cloud for analysis – forced to AWS for this deployment.
    default_cloud: str = Field(default="aws", env="DEFAULT_CLOUD")

    # Neo4j Configuration (must come from environment, not hardcoded)
    neo4j_uri: str = Field(default="", env="NEO4J_URI")
    neo4j_user: str = Field(default="", env="NEO4J_USER")
    neo4j_password: str = Field(default="", env="NEO4J_PASSWORD")

    # AWS Configuration
    aws_access_key_id: Optional[str] = Field(default=None, env="AWS_ACCESS_KEY_ID")
    aws_secret_access_key: Optional[str] = Field(default=None, env="AWS_SECRET_ACCESS_KEY")
    aws_region: str = Field(default="us-east-1", env="AWS_REGION")

    # Azure AD Configuration (kept for backwards compatibility but unused at runtime)
    azure_tenant_id: Optional[str] = Field(default=None, env="AZURE_TENANT_ID")
    azure_client_id: Optional[str] = Field(default=None, env="AZURE_CLIENT_ID")
    azure_client_secret: Optional[str] = Field(default=None, env="AZURE_CLIENT_SECRET")

    # GCP Configuration (kept for backwards compatibility but unused at runtime)
    gcp_project_id: Optional[str] = Field(default=None, env="GCP_PROJECT_ID")
    gcp_credentials_path: Optional[str] = Field(default=None, env="GCP_CREDENTIALS_PATH")

    # LLM Configuration (LLM is optional and may be disabled)
    llm_provider: str = Field(default="azure_openai", env="LLM_PROVIDER")
    azure_openai_endpoint: Optional[str] = Field(default=None, env="AZURE_OPENAI_ENDPOINT")
    azure_openai_api_key: Optional[str] = Field(default=None, env="AZURE_OPENAI_API_KEY")
    azure_openai_deployment_name: str = Field(default="gpt-4", env="AZURE_OPENAI_DEPLOYMENT_NAME")
    aws_bedrock_region: str = Field(default="us-east-1", env="AWS_BEDROCK_REGION")
    aws_bedrock_model_id: str = Field(
        default="anthropic.claude-3-sonnet-20240229-v1:0",
        env="AWS_BEDROCK_MODEL_ID",
    )

    # Application Configuration
    log_level: str = Field(default="INFO", env="LOG_LEVEL")
    environment: str = Field(default="development", env="ENVIRONMENT")

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


# Global settings instance
settings = Settings()

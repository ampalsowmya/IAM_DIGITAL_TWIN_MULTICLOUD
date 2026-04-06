"""Pydantic v2 API models."""

from typing import Any

from pydantic import BaseModel, Field


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class IngestResponse(BaseModel):
    status: str
    roles_ingested: int
    relationships_created: int
    cloud: str


class IngestProgress(BaseModel):
    status: str
    percent: float
    roles_processed: int
    total_roles: int
    last_scan_utc: str = ""


class GraphNode(BaseModel):
    id: str
    name: str
    type: str
    risk_score: float = 0.0
    cloud: str = "aws"


class GraphEdge(BaseModel):
    source: str
    target: str
    relationship: str


class GraphResponse(BaseModel):
    nodes: list[GraphNode]
    edges: list[GraphEdge]


class EscalationPath(BaseModel):
    from_role: str
    to_role: str
    path: list[str]
    risk_level: str


class RiskScore(BaseModel):
    identity_id: str
    name: str
    cloud: str
    risk_score: int
    level: str
    if_score: float
    anomaly: bool
    permissions_count: int
    escalation_paths: int


class HealthStatus(BaseModel):
    aws: bool
    neo4j: bool
    ml_models: bool
    overall: bool
    details: dict[str, Any] = Field(default_factory=dict)


class TokenForm(BaseModel):
    username: str
    password: str


class WhatIfFeatures(BaseModel):
    permissions_count: int = Field(default=10, ge=0, le=100000)
    has_admin_policy: int = Field(default=0, ge=0, le=1)
    has_star_action: int = Field(default=0, ge=0, le=1)
    trust_account_count: int = Field(default=0, ge=0, le=10000)
    cross_account: int = Field(default=0, ge=0, le=1)
    age_days: int = Field(default=30, ge=0, le=36500)
    inline_policy_count: int = Field(default=0, ge=0, le=1000)
    managed_policy_count: int = Field(default=0, ge=0, le=1000)


class ComplianceViolation(BaseModel):
    role_arn: str
    role_name: str
    cloud: str
    rule_id: str
    rule_name: str
    severity: str
    detail: str

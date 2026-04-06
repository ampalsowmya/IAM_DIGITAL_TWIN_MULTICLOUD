"""Service health checks."""

from __future__ import annotations

import boto3
from botocore.exceptions import BotoCoreError, ClientError
from fastapi import APIRouter

from config import get_settings
from graph_store import get_driver
from ml_engine import models_ready, train_models
from models import HealthStatus

router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthStatus)
async def health():
    settings = get_settings()
    details: dict[str, str] = {}

    aws_ok = False
    try:
        session_kw: dict = {"region_name": settings.aws_region}
        if settings.aws_access_key_id and settings.aws_secret_access_key:
            session_kw["aws_access_key_id"] = settings.aws_access_key_id
            session_kw["aws_secret_access_key"] = settings.aws_secret_access_key
        sess = boto3.session.Session(**session_kw)
        sess.client("iam").get_account_summary()
        aws_ok = True
    except (ClientError, BotoCoreError, ValueError) as e:
        details["aws"] = str(e)

    neo_ok = False
    try:
        drv = get_driver()
        drv.verify_connectivity()
        neo_ok = True
    except (OSError, RuntimeError, ValueError) as e:
        details["neo4j"] = str(e)

    ml_ok = models_ready()
    if not ml_ok:
        try:
            train_models()
            ml_ok = models_ready()
        except Exception as e:
            details["ml_models"] = str(e)
            ml_ok = False

    # Core platform healthy if Neo4j responds; AWS/ML may be degraded in dev
    overall = bool(neo_ok)
    return HealthStatus(
        aws=aws_ok,
        neo4j=neo_ok,
        ml_models=ml_ok,
        overall=overall,
        details=details,
    )

"""IAM Digital Twin — FastAPI application entrypoint."""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from apscheduler.schedulers.background import BackgroundScheduler
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from auth import router as auth_router
from config import get_settings
from graph_store import (
    close_driver,
    get_driver,
    init_driver,
    init_schema,
    router as graph_router,
    wait_for_neo4j,
)
from health import router as health_router
from ingestion import ingest_aws_iam, log_activity, router as ingest_router
from ml_engine import train_models
from risk import compliance_router, router as risk_router

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

scheduler: BackgroundScheduler | None = None


def _scheduled_ingest():
    try:
        ingest_aws_iam()
    except Exception as e:
        logger.exception("Scheduled ingest failed: %s", e)


@asynccontextmanager
async def lifespan(app: FastAPI):
    global scheduler
    settings = get_settings()

    # 1. Neo4j driver
    init_driver(settings.neo4j_uri, settings.neo4j_user, settings.neo4j_password)
    drv = get_driver()

    # 2. Wait for DB (avoids race with docker-compose)
    try:
        await wait_for_neo4j(drv, retries=12, delay=3.0)
    except Exception as e:
        logger.exception("Neo4j wait failed: %s", e)
        close_driver()
        raise

    # 3. Schema
    with drv.session() as session:
        init_schema(session)

    # 4–7. ML last; failures must not crash the app
    try:
        ok = train_models()
        if ok:
            log_activity(
                "info",
                "ML models retrained",
                "RF + XGB + Isolation Forest loaded",
            )
        else:
            log_activity(
                "warn",
                "ML models unavailable",
                "Risk scoring will use fallback values until training succeeds",
            )
    except Exception as e:
        logger.exception("ML startup error (non-fatal): %s", e)
        log_activity("error", "ML training error", str(e))

    scheduler = BackgroundScheduler()
    scheduler.add_job(
        _scheduled_ingest,
        "interval",
        seconds=max(60, settings.ingest_interval_seconds),
        id="aws_ingest",
        replace_existing=True,
    )
    scheduler.start()
    logger.info("APScheduler started: ingest every %s s", settings.ingest_interval_seconds)

    yield

    if scheduler:
        scheduler.shutdown(wait=False)
    close_driver()


def create_app() -> FastAPI:
    app = FastAPI(
        title="IAM Digital Twin",
        description="AI Risk Intelligence Platform — AWS IAM, Neo4j, ML scoring",
        version="1.0.0",
        docs_url="/docs",
        redoc_url="/redoc",
        lifespan=lifespan,
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    api = "/api/v1"
    app.include_router(health_router, prefix=api)
    app.include_router(auth_router, prefix=api)
    app.include_router(ingest_router, prefix=api)
    app.include_router(graph_router, prefix=api)
    app.include_router(risk_router, prefix=api)
    app.include_router(compliance_router, prefix=api)

    return app


app = create_app()

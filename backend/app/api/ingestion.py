import asyncio
from typing import Dict, Literal

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from ..graph.ingest import ingest_entities
from ..graph.neo4j_client import get_neo4j_client
from ..iam_ingestion import ingest_aws_iam, ingest_azure_iam, ingest_gcp_iam
from .deps import get_current_user

router = APIRouter(prefix="/ingest", tags=["ingestion"])
progress_state: Dict[str, str] = {"status": "idle"}


class IngestResponse(BaseModel):
    status: str
    cloud: str
    count: int


async def _run_ingestion(cloud: str) -> None:
    progress_state["status"] = f"running:{cloud}"
    if cloud == "aws":
        entities = ingest_aws_iam()
    elif cloud == "azure":
        entities = ingest_azure_iam()
    elif cloud == "gcp":
        entities = ingest_gcp_iam()
    else:
        entities = []
    await ingest_entities(get_neo4j_client(), entities)
    progress_state["status"] = f"done:{cloud}:{len(entities)}"


@router.post("/{cloud}", response_model=IngestResponse)
async def ingest_cloud(
    cloud: Literal["aws", "azure", "gcp"],
    background_tasks: BackgroundTasks,
    user=Depends(get_current_user),
):
    """
    Start cloud IAM ingestion in background.

    Example response:
    {"status":"started","cloud":"aws","count":0}
    """
    background_tasks.add_task(_run_ingestion, cloud)
    return IngestResponse(status="started", cloud=cloud, count=0)


@router.get("/progress")
async def ingest_progress(user=Depends(get_current_user)):
    """
    Stream ingestion status updates via SSE.

    Example event data:
    data: {"status":"running:aws"}
    """

    async def event_stream():
        while True:
            yield f"data: {progress_state}\n\n"
            await asyncio.sleep(1)

    return StreamingResponse(event_stream(), media_type="text/event-stream")


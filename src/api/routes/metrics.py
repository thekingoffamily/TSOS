from __future__ import annotations

from fastapi import APIRouter, Response
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest

from src.services.metrics import METRIC_REGISTRY

router = APIRouter(tags=["metrics"])


@router.get("/metrics")
async def prometheus_metrics() -> Response:
    data = generate_latest(METRIC_REGISTRY)
    return Response(content=data, media_type=CONTENT_TYPE_LATEST)

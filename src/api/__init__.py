from fastapi import APIRouter, Depends

from .dependencies import require_bearer_token
from .routes.analyze import router as analyze_router
from .routes.metrics import router as metrics_router


def create_api_router() -> APIRouter:
    router = APIRouter()
    router.include_router(
        analyze_router,
        prefix="/api/v1",
        dependencies=[Depends(require_bearer_token)],
    )
    router.include_router(metrics_router)
    return router


__all__ = ["create_api_router"]

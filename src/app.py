from __future__ import annotations

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from src.api import create_api_router
from src.logger import get_logger
from src.schemes import ErrorCode, ErrorResponse

logger = get_logger(__name__)


def create_app() -> FastAPI:
    app = FastAPI(title="TSOS Video Analyzer", version="0.1.0")

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(create_api_router())

    @app.exception_handler(HTTPException)
    async def http_exception_handler(
        request: Request,
        exc: HTTPException,
    ):  # type: ignore[override]
        detail = exc.detail
        if isinstance(detail, dict) and "code" in detail:
            body = ErrorResponse(**detail)
        else:
            body = ErrorResponse(code=ErrorCode.UNKNOWN, detail=str(detail))
        return JSONResponse(status_code=exc.status_code, content=body.model_dump())

    return app


app = create_app()

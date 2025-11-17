from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel

from src.models import VideoStatus
from src.schemes.errors import ErrorCode


class AnalyzeResponse(BaseModel):
    task_id: uuid.UUID
    status: VideoStatus


class VideoStatusResponse(BaseModel):
    id: uuid.UUID
    status: VideoStatus
    original_filename: str
    provider: str | None = None
    unique_people: int | None = None
    summary: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None
    error_message: str | None = None

    class Config:
        from_attributes = True


class ErrorResponse(BaseModel):
    code: ErrorCode
    detail: str

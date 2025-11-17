from __future__ import annotations

import uuid
from pathlib import Path

from fastapi import APIRouter, BackgroundTasks, File, HTTPException, UploadFile, status

from src.db import session_scope
from src.models import Video, VideoStatus
from src.schemes import AnalyzeResponse, ErrorCode, ErrorResponse, VideoStatusResponse
from src.services.video_processor import process_video_task

BASE_DIR = Path(__file__).resolve().parents[3]
MEDIA_DIR = BASE_DIR / "media"
UPLOAD_DIR = MEDIA_DIR / "uploads"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

router = APIRouter(tags=["videos"])


def save_upload_file(upload: UploadFile) -> Path:
    suffix = Path(upload.filename or "video.mp4").suffix or ".mp4"
    target_path = UPLOAD_DIR / f"{uuid.uuid4()}{suffix}"
    with open(target_path, "wb") as buffer:
        content = upload.file.read()
        buffer.write(content)
    return target_path


@router.post(
    "/analyze",
    response_model=AnalyzeResponse,
    responses={400: {"model": ErrorResponse}, 500: {"model": ErrorResponse}},
)
async def analyze_video(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
) -> AnalyzeResponse:
    if not file.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": ErrorCode.INVALID_REQUEST, "detail": "Filename missing"},
        )

    stored_path = save_upload_file(file).resolve()
    with session_scope() as session:
        video = Video(
            original_filename=file.filename,
            stored_path=str(stored_path),
            status=VideoStatus.RECEIVED,
        )
        session.add(video)
        session.flush()
        video_id = video.id

    background_tasks.add_task(process_video_task, video_id)

    return AnalyzeResponse(task_id=video_id, status=VideoStatus.RECEIVED)


@router.get(
    "/tasks/{task_id}",
    response_model=VideoStatusResponse,
    responses={404: {"model": ErrorResponse}},
)
async def get_task_status(task_id: uuid.UUID) -> VideoStatusResponse:
    with session_scope() as session:
        video = session.get(Video, task_id)
        if video is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"code": ErrorCode.VIDEO_NOT_FOUND, "detail": "Task not found"},
            )
        session.refresh(video)

    return VideoStatusResponse.from_orm(video)

from __future__ import annotations

import asyncio
import re
import time
import uuid
from pathlib import Path
from typing import List, Optional

import cv2

from src.db import session_scope
from src.logger import get_logger
from src.models import Video, VideoMetric, VideoStatus
from src.providers.openrouter import OpenRouterClient
from src.schemes import ErrorCode
from src.services.metrics import (
    PROCESSING_TIME,
    VIDEOS_FAILED,
    VIDEOS_IN_PROGRESS,
    VIDEOS_PROCESSED,
)
from src.settings import get_settings
from src.utils.aiohttp_adapter import AioHttpAdapterError

logger = get_logger(__name__)

BASE_DIR = Path(__file__).resolve().parents[2]
MEDIA_DIR = BASE_DIR / "media"
FRAME_DIR = MEDIA_DIR / "frames"
FRAME_DIR.mkdir(parents=True, exist_ok=True)


def run_coroutine_sync(coro):
    return asyncio.run(coro)


def detect_motion_frames(video_path: str, max_frames: int = 5) -> tuple[List[Path], int, float]:
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        raise RuntimeError("Cannot open video file")

    fps = cap.get(cv2.CAP_PROP_FPS) or 24.0
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0)
    duration = total_frames / fps if fps else 0

    prev_gray = None
    saved_frames: List[Path] = []
    frame_index = 0

    while cap.isOpened() and len(saved_frames) < max_frames:
        ret, frame = cap.read()
        if not ret:
            break
        frame_index += 1
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        gray = cv2.GaussianBlur(gray, (21, 21), 0)
        if prev_gray is None:
            prev_gray = gray
            continue
        diff = cv2.absdiff(prev_gray, gray)
        thresh = cv2.threshold(diff, 25, 255, cv2.THRESH_BINARY)[1]
        movement_score = thresh.mean()
        if movement_score > 2.0 and frame_index % int(fps) == 0:
            frame_path = FRAME_DIR / f"{uuid.uuid4()}.jpg"
            cv2.imwrite(str(frame_path), frame)
            saved_frames.append(frame_path)
        prev_gray = gray

    cap.release()
    return saved_frames, total_frames, duration


def parse_people_count(text: str) -> int:
    match = re.search(r"(\d+)", text)
    if match:
        return int(match.group(1))
    return 0


def cleanup_frames(frames: List[Path]) -> None:
    for frame in frames:
        try:
            frame.unlink(missing_ok=True)
        except Exception:
            logger.warning("Failed to remove frame %s", frame)


def process_video_task(video_id: uuid.UUID) -> None:
    start_time = time.perf_counter()
    VIDEOS_IN_PROGRESS.inc()
    logger.info("Processing started for video %s", video_id)

    with session_scope() as session:
        video = session.get(Video, video_id)
        if video is None:
            logger.error("Video %s not found", video_id)
            return
        video.status = VideoStatus.PROCESSING
        session.add(video)

    frames: List[Path] = []
    descriptions: List[str] = []
    unique_people = 0
    provider_name: Optional[str] = None

    try:
        frames, total_frames, duration = detect_motion_frames(video.stored_path)
        settings = get_settings()

        if settings.OPENROUTER_API_KEY:
            client = OpenRouterClient(
                api_key=settings.OPENROUTER_API_KEY,
            )
            provider_name = "openrouter"
            summary_prompt = settings.SUMMARY_PROMPT
            people_prompt = settings.PEOPLE_COUNT_PROMPT
            for frame_path in frames:
                summary_response = run_coroutine_sync(
                    client.describe_image(
                        image_path=str(frame_path),
                        prompt=summary_prompt,
                    )
                )
                descriptions.append(summary_response)

                retry_attempts = 0
                while True:
                    try:
                        count_response = run_coroutine_sync(
                            client.describe_image(
                                image_path=str(frame_path),
                                prompt=people_prompt,
                            )
                        )
                        break
                    except AioHttpAdapterError as count_exc:
                        retry_attempts += 1
                        if retry_attempts > 2 or count_exc.code != ErrorCode.AI_PROVIDER_TIMEOUT:
                            raise
                        logger.info(
                            "Retrying people count for frame %s due to timeout (%s)",
                            frame_path.name,
                            retry_attempts,
                        )
                        time.sleep(2)

                unique_people = max(unique_people, parse_people_count(count_response))
        else:
            logger.info("No AI providers configured, skipping description phase.")

        summary_text = " | ".join(descriptions) if descriptions else None

        with session_scope() as session:
            video = session.get(Video, video_id)
            if video is None:
                raise RuntimeError("Video record missing during update.")
            video.status = VideoStatus.COMPLETED
            video.provider = provider_name
            video.unique_people = unique_people
            video.total_frames = total_frames
            video.duration_seconds = duration
            video.analysis_time = time.perf_counter() - start_time
            video.summary = summary_text
            session.add(video)

            metric = VideoMetric(video_id=video_id, name="unique_people", value=unique_people)
            session.add(metric)

        VIDEOS_PROCESSED.inc()
        PROCESSING_TIME.observe(time.perf_counter() - start_time)
        logger.info("Processing finished for video %s", video_id)

    except AioHttpAdapterError as exc:
        logger.warning("Provider error for video %s: %s", video_id, exc)
        with session_scope() as session:
            video = session.get(Video, video_id)
            if video:
                video.status = VideoStatus.FAILED
                video.error_message = f"Provider error ({exc.status}): {exc}"
                session.add(video)
        VIDEOS_FAILED.inc()

    except Exception as exc:
        logger.exception("Video processing failed: %s", exc)
        with session_scope() as session:
            video = session.get(Video, video_id)
            if video:
                video.status = VideoStatus.FAILED
                video.error_message = str(exc)
                session.add(video)
        VIDEOS_FAILED.inc()
    finally:
        cleanup_frames(frames)


__all__ = ["process_video_task"]

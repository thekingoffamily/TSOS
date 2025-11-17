from __future__ import annotations

from pathlib import Path
from typing import Any, Optional

import ffmpeg

from src.logger import get_logger
from src.schemes import ErrorCode

logger = get_logger(__name__)


class FFmpegError(RuntimeError):
    def __init__(self, code: ErrorCode, message: str, *, detail: str | None = None):
        self.code = code
        self.detail = detail
        super().__init__(message)


class FFmpegVideoHelper:
    """Utility wrapper around python-ffmpeg for common video operations."""

    def __init__(self) -> None:
        self._ffmpeg = ffmpeg

    def probe(self, video_path: str) -> dict[str, Any]:
        path = self._ensure_path(video_path)
        try:
            return self._ffmpeg.probe(str(path))
        except ffmpeg.Error as exc:
            logger.error("ffmpeg probe failed for %s: %s", path, exc.stderr)
            raise FFmpegError(ErrorCode.VIDEO_DECODING_FAILED, "Failed to probe video.") from exc

    def extract_frame(
        self,
        video_path: str,
        output_path: str,
        *,
        timestamp: float = 0.0,
        width: Optional[int] = None,
        height: Optional[int] = None,
    ) -> Path:
        path = self._ensure_path(video_path)
        output = Path(output_path)
        output.parent.mkdir(parents=True, exist_ok=True)

        stream = self._ffmpeg.input(str(path), ss=timestamp)
        if width or height:
            stream = stream.filter("scale", width or -1, height or -1)
        stream = stream.output(str(output), vframes=1)

        self._run(stream, f"extract_frame {path.name}@{timestamp}s")
        return output

    def transcode(
        self,
        video_path: str,
        output_path: str,
        *,
        video_codec: str = "libx264",
        audio_codec: Optional[str] = "aac",
        crf: int = 23,
        preset: str = "medium",
    ) -> Path:
        path = self._ensure_path(video_path)
        output = Path(output_path)
        output.parent.mkdir(parents=True, exist_ok=True)

        stream = self._ffmpeg.input(str(path))
        stream = stream.output(
            str(output),
            vcodec=video_codec,
            acodec=audio_codec if audio_codec else "copy",
            crf=crf,
            preset=preset,
        )
        self._run(stream, f"transcode {path.name} -> {output.suffix}")
        return output

    def clip_segment(
        self,
        video_path: str,
        output_path: str,
        *,
        start: float,
        duration: float,
    ) -> Path:
        path = self._ensure_path(video_path)
        output = Path(output_path)
        output.parent.mkdir(parents=True, exist_ok=True)

        stream = self._ffmpeg.input(str(path), ss=start, t=duration)
        stream = stream.output(str(output), c="copy")
        self._run(stream, f"clip {path.name} {start}-{start + duration}s")
        return output

    def _run(self, stream: ffmpeg.nodes.FilterableStream, operation: str) -> None:
        try:
            stream.run(capture_stdout=True, capture_stderr=True, overwrite_output=True)
            logger.info("ffmpeg %s completed.", operation)
        except ffmpeg.Error as exc:
            detail = exc.stderr.decode("utf-8", errors="ignore") if exc.stderr else None
            logger.error("ffmpeg %s failed: %s", operation, detail)
            raise FFmpegError(
                ErrorCode.VIDEO_DECODING_FAILED,
                f"FFmpeg failed to {operation}.",
                detail=detail,
            ) from exc

    @staticmethod
    def _ensure_path(video_path: str) -> Path:
        path = Path(video_path)
        if not path.exists():
            raise FFmpegError(
                ErrorCode.VIDEO_NOT_FOUND,
                f"Video file not found: {video_path}",
            )
        return path.resolve()


__all__ = ["FFmpegVideoHelper", "FFmpegError"]

from __future__ import annotations

import enum
import uuid
from typing import Optional

from sqlalchemy import Enum, Float, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import mapped_column, Mapped, relationship

from .base import Base, TimestampMixin, TableNameMixin


class VideoStatus(str, enum.Enum):
    RECEIVED = "received"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class Video(TableNameMixin, Base, TimestampMixin):
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    original_filename: Mapped[str] = mapped_column(String(255))
    stored_path: Mapped[str] = mapped_column(String(512))
    status: Mapped[VideoStatus] = mapped_column(
        Enum(VideoStatus),
        default=VideoStatus.RECEIVED,
    )
    provider: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    total_frames: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    duration_seconds: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    unique_people: Mapped[int] = mapped_column(Integer, default=0)
    analysis_time: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    summary: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    metrics: Mapped[list["VideoMetric"]] = relationship(
        "VideoMetric",
        back_populates="video",
        cascade="all, delete-orphan",
    )


class VideoMetric(TableNameMixin, Base, TimestampMixin):
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    video_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("video.id", ondelete="CASCADE"),
    )
    name: Mapped[str] = mapped_column(String(128))
    value: Mapped[float] = mapped_column(Float)

    video: Mapped[Video] = relationship("Video", back_populates="metrics")

from __future__ import annotations

from prometheus_client import Counter, Histogram, CollectorRegistry

REGISTRY = CollectorRegistry()

VIDEOS_PROCESSED = Counter(
    "tsos_videos_processed_total",
    "Total number of processed videos",
    registry=REGISTRY,
)
VIDEOS_FAILED = Counter(
    "tsos_videos_failed_total",
    "Total number of failed video analyses",
    registry=REGISTRY,
)
VIDEOS_IN_PROGRESS = Counter(
    "tsos_videos_started_total",
    "Total number of videos started for processing",
    registry=REGISTRY,
)
PROCESSING_TIME = Histogram(
    "tsos_video_processing_seconds",
    "Video processing time in seconds",
    registry=REGISTRY,
)

METRIC_REGISTRY = REGISTRY


__all__ = [
    "VIDEOS_PROCESSED",
    "VIDEOS_FAILED",
    "VIDEOS_IN_PROGRESS",
    "PROCESSING_TIME",
    "METRIC_REGISTRY",
]

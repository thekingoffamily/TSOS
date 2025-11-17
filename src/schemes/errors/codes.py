from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from http import HTTPStatus
from typing import Dict


class ErrorCode(str, Enum):
    """Canonical error codes for TSOS services."""

    UNKNOWN = "E000"
    INVALID_REQUEST = "E050"
    VIDEO_NOT_FOUND = "E100"
    VIDEO_DECODING_FAILED = "E101"
    AI_PROVIDER_UNAVAILABLE = "E200"
    AI_PROVIDER_TIMEOUT = "E201"
    INVALID_TRIGGER_CONFIG = "E300"
    AUTHORIZATION_FAILED = "E400"


@dataclass(frozen=True)
class ErrorDescriptor:
    code: ErrorCode
    message: str
    http_status: HTTPStatus = HTTPStatus.INTERNAL_SERVER_ERROR


ERROR_MESSAGES: Dict[ErrorCode, ErrorDescriptor] = {
    ErrorCode.UNKNOWN: ErrorDescriptor(
        code=ErrorCode.UNKNOWN,
        message="Unexpected error occurred.",
    ),
    ErrorCode.INVALID_REQUEST: ErrorDescriptor(
        code=ErrorCode.INVALID_REQUEST,
        message="Request parameters are invalid.",
        http_status=HTTPStatus.BAD_REQUEST,
    ),
    ErrorCode.VIDEO_NOT_FOUND: ErrorDescriptor(
        code=ErrorCode.VIDEO_NOT_FOUND,
        message="Requested video file was not found.",
        http_status=HTTPStatus.NOT_FOUND,
    ),
    ErrorCode.VIDEO_DECODING_FAILED: ErrorDescriptor(
        code=ErrorCode.VIDEO_DECODING_FAILED,
        message="Video decoding or preprocessing failed.",
        http_status=HTTPStatus.UNPROCESSABLE_ENTITY,
    ),
    ErrorCode.AI_PROVIDER_UNAVAILABLE: ErrorDescriptor(
        code=ErrorCode.AI_PROVIDER_UNAVAILABLE,
        message="AI provider is unavailable or misconfigured.",
        http_status=HTTPStatus.BAD_GATEWAY,
    ),
    ErrorCode.AI_PROVIDER_TIMEOUT: ErrorDescriptor(
        code=ErrorCode.AI_PROVIDER_TIMEOUT,
        message="AI provider did not respond in time.",
        http_status=HTTPStatus.GATEWAY_TIMEOUT,
    ),
    ErrorCode.INVALID_TRIGGER_CONFIG: ErrorDescriptor(
        code=ErrorCode.INVALID_TRIGGER_CONFIG,
        message="Trigger configuration is invalid.",
        http_status=HTTPStatus.BAD_REQUEST,
    ),
    ErrorCode.AUTHORIZATION_FAILED: ErrorDescriptor(
        code=ErrorCode.AUTHORIZATION_FAILED,
        message="Authorization failed for the requested resource.",
        http_status=HTTPStatus.UNAUTHORIZED,
    ),
}


def describe_error(code: ErrorCode) -> ErrorDescriptor:
    """Return the descriptor for the provided error code."""

    return ERROR_MESSAGES.get(code, ERROR_MESSAGES[ErrorCode.UNKNOWN])

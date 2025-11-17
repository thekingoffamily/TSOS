from __future__ import annotations

import logging
from logging import (
    Formatter,
    Logger,
    StreamHandler
)
from typing import Optional


LOG_LEVEL = logging.INFO
LOG_FORMAT = (
    "%(asctime)s | %(levelname)-8s | %(name)s | %(module)s:%(lineno)d | %(message)s"
)
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

_default_logger_name = "TSOS"
_configured_loggers: dict[str, Logger] = {}


def _build_handler() -> StreamHandler:
    handler = StreamHandler()
    handler.setFormatter(Formatter(LOG_FORMAT, DATE_FORMAT))
    handler.setLevel(LOG_LEVEL)
    return handler


def _configure_logger(name: str) -> Logger:
    logger = logging.getLogger(name)

    if not logger.handlers:
        handler = _build_handler()
        logger.addHandler(handler)
        logger.setLevel(LOG_LEVEL)
        logger.propagate = False

    _configured_loggers[name] = logger
    return logger


def get_logger(name: Optional[str] = None) -> Logger:
    """Return a console-configured logger.

    If the logger has already been configured via this module, the same instance is returned.
    """

    logger_name = name or _default_logger_name
    if logger_name in _configured_loggers:
        return _configured_loggers[logger_name]

    return _configure_logger(logger_name)

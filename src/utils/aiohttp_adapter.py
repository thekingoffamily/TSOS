from __future__ import annotations

import asyncio
from typing import Any, Mapping, Optional

import aiohttp

from src.logger import get_logger
from src.schemes import ErrorCode

logger = get_logger(__name__)


class AioHttpAdapterError(RuntimeError):
    def __init__(self, code: ErrorCode, message: str, *, status: int | None = None):
        self.code = code
        self.status = status
        super().__init__(message)


class AioHttpAdapter:
    def __init__(self, *, timeout: float = 30.0, max_retries: int = 0, retry_delay: float = 0.5):
        self.timeout = timeout
        self.max_retries = max_retries
        self.retry_delay = retry_delay

    async def _request(
        self,
        method: str,
        url: str,
        *,
        headers: Optional[Mapping[str, str]] = None,
        json: Any = None,
    ) -> dict[str, Any]:
        attempt = 0

        while True:
            attempt += 1
            try:
                timeout = aiohttp.ClientTimeout(total=self.timeout)
                async with aiohttp.ClientSession(timeout=timeout) as session:
                    async with session.request(method, url, headers=headers, json=json) as response:
                        payload = await response.json(content_type=None)
                        if response.status >= 400:
                            logger.error(
                                "HTTP error from %s %s status=%s body=%s",
                                method,
                                url,
                                response.status,
                                payload,
                            )
                            raise AioHttpAdapterError(
                                ErrorCode.AI_PROVIDER_UNAVAILABLE,
                                f"HTTP {response.status} error",
                                status=response.status,
                            )
                        return payload
            except asyncio.TimeoutError as exc:
                logger.warning("Request to %s timed out: %s", url, exc)
                error = AioHttpAdapterError(
                    ErrorCode.AI_PROVIDER_TIMEOUT,
                    "Request timed out",
                )
            except aiohttp.ClientError as exc:
                logger.warning("Aiohttp client error %s: %s", url, exc)
                error = AioHttpAdapterError(
                    ErrorCode.AI_PROVIDER_UNAVAILABLE,
                    "Network error",
                )
            except ValueError as exc:
                logger.error("Failed to decode response: %s", exc)
                raise AioHttpAdapterError(
                    ErrorCode.AI_PROVIDER_UNAVAILABLE,
                    "Invalid response payload",
                ) from exc
            else:
                return  # pragma: no cover

            if attempt > self.max_retries:
                raise error

            await asyncio.sleep(self.retry_delay)

    async def post(
        self,
        url: str,
        *,
        headers: Optional[Mapping[str, str]] = None,
        json: Any = None,
    ) -> dict[str, Any]:
        return await self._request("POST", url, headers=headers, json=json)


__all__ = ["AioHttpAdapter", "AioHttpAdapterError"]

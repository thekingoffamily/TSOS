from __future__ import annotations

import asyncio
import base64
from pathlib import Path
from typing import Any, Iterable, Optional

from src.logger import get_logger
from src.settings import get_settings
from src.utils.aiohttp_adapter import AioHttpAdapter, AioHttpAdapterError


DEFAULT_BASE_URL = "https://openrouter.ai/api/v1"
DEFAULT_REFERER = "http://localhost:8000"
DEFAULT_TITLE = "TSOS"

logger = get_logger(__name__)


def _encode_image(image_path: Path) -> str:
    mime_map = {
        ".png": "image/png",
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".webp": "image/webp",
        ".gif": "image/gif",
    }
    suffix = image_path.suffix.lower()
    mime = mime_map.get(suffix, "image/jpeg")
    data = image_path.read_bytes()
    encoded = base64.b64encode(data).decode("utf-8")
    return f"data:{mime};base64,{encoded}"


class OpenRouterError(RuntimeError):
    pass


class OpenRouterClient:
    def __init__(
        self,
        *,
        api_key: Optional[str] = None,
        base_url: str = DEFAULT_BASE_URL,
        referer: str = DEFAULT_REFERER,
        site_title: str = DEFAULT_TITLE,
        adapter: Optional[AioHttpAdapter] = None,
        cooldown_seconds: float = 1.5,
    ):
        settings = get_settings()
        self.api_key = api_key or settings.OPENROUTER_API_KEY

        if not self.api_key:
            raise OpenRouterError("OPENROUTER_API_KEY is not configured.")

        self.base_url = base_url.rstrip("/")
        self.referer = referer
        self.site_title = site_title
        self.adapter = adapter or AioHttpAdapter(max_retries=2, retry_delay=1.0)
        self.cooldown_seconds = cooldown_seconds

    @property
    def _headers(self) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": self.referer,
            "X-Title": self.site_title,
        }

    async def describe_image(
        self,
        image_path: str,
        *,
        prompt: str,
        model: str = "mistralai/mistral-small-3.2-24b-instruct:free",
        max_retries: int = 3,
        retry_delay: float = 1.0,
    ) -> str:
        path = Path(image_path)
        if not path.exists():
            raise OpenRouterError(f"Image file not found: {image_path}")

        data_uri = _encode_image(path)
        payload = {
            "model": model,
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {"type": "image_url", "image_url": {"url": data_uri}},
                    ],
                }
            ],
        }

        attempt = 0
        while attempt < max_retries:
            attempt += 1
            try:
                if attempt > 1:
                    logger.info(
                        "Cooling down before retry (%ss)",
                        self.cooldown_seconds,
                    )
                    await asyncio.sleep(self.cooldown_seconds)
                logger.info("Calling OpenRouter (%s/%s)", attempt, max_retries)
                response = await self.adapter.post(
                    f"{self.base_url}/chat/completions",
                    headers=self._headers,
                    json=payload,
                )
                return self._extract_content(response)
            except (AioHttpAdapterError, OpenRouterError) as exc:
                logger.warning("OpenRouter request failed: %s", exc)
                if attempt >= max_retries:
                    raise
                backoff = retry_delay * attempt
                if isinstance(exc, AioHttpAdapterError) and exc.status == 429:
                    backoff += self.cooldown_seconds
                await asyncio.sleep(backoff)

        raise OpenRouterError("Failed to describe image after retries.")

    @staticmethod
    def _extract_content(response: dict[str, Any]) -> str:
        choices: Iterable[dict[str, Any]] = response.get("choices", [])
        for choice in choices:
            message = choice.get("message")
            if not message:
                continue
            content = message.get("content")
            if isinstance(content, str):
                return content
            if isinstance(content, list):
                texts = [item.get("text") for item in content if "text" in item]
                combined = "\n".join(filter(None, texts))
                if combined:
                    return combined
        raise OpenRouterError("No content returned from OpenRouter.")


__all__ = ["OpenRouterClient", "OpenRouterError"]

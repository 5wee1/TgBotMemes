"""
Image generation provider — swap this file to change the backend.
Implement generate_image() and the rest of the bot stays unchanged.
"""
import asyncio
import logging
from typing import Optional

import httpx

from config import config

logger = logging.getLogger(__name__)


class ImageGenerationError(Exception):
    pass


class ImageProvider:
    def __init__(self):
        self.base_url = config.image_api_base_url.rstrip("/")
        self.api_key = config.image_api_key
        self.model = config.image_model
        self.timeout = config.timeout_seconds
        self.retries = config.retries

    async def generate_image(
        self,
        prompt: str,
        size: str = "1024x1024",
        seed: Optional[int] = None,
        quality: str = "standard",
    ) -> str:
        """
        Returns a URL (or base64 data URI) of the generated image.
        Raises ImageGenerationError on failure after retries.
        """
        payload = self._build_payload(prompt, size, seed, quality)
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        last_error: Exception = Exception("unknown")
        for attempt in range(self.retries + 1):
            try:
                async with httpx.AsyncClient(timeout=self.timeout) as client:
                    resp = await client.post(
                        f"{self.base_url}/images/generations",
                        json=payload,
                        headers=headers,
                    )
                    resp.raise_for_status()
                    return self._parse_response(resp.json())
            except httpx.HTTPStatusError as e:
                last_error = e
                logger.warning("ImageAPI HTTP %s attempt %d/%d", e.response.status_code, attempt + 1, self.retries + 1)
                if e.response.status_code in (400, 401, 403):
                    break  # non-retryable
            except Exception as e:
                last_error = e
                logger.warning("ImageAPI error attempt %d/%d: %s", attempt + 1, self.retries + 1, e)

            if attempt < self.retries:
                await asyncio.sleep(2 ** attempt)

        raise ImageGenerationError(f"Failed after {self.retries + 1} attempts: {last_error}") from last_error

    def _build_payload(self, prompt: str, size: str, seed: Optional[int], quality: str) -> dict:
        payload: dict = {
            "model": self.model,
            "prompt": prompt,
            "n": 1,
            "size": size,
        }
        # OpenAI-compatible quality param
        if quality in ("standard", "hd"):
            payload["quality"] = quality
        # Some APIs accept seed
        if seed is not None:
            payload["seed"] = seed
        return payload

    def _parse_response(self, data: dict) -> str:
        # OpenAI-compatible: data.data[0].url or b64_json
        items = data.get("data", [])
        if not items:
            raise ImageGenerationError("Empty response from image API")
        item = items[0]
        if "url" in item:
            return item["url"]
        if "b64_json" in item:
            return "data:image/png;base64," + item["b64_json"]
        raise ImageGenerationError(f"Unexpected response format: {list(item.keys())}")


# Singleton
image_provider = ImageProvider()

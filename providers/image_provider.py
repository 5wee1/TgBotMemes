"""
Image provider — OpenAI GPT Image 1.5.
Swap this file to change the backend.
"""
import asyncio
import base64
import logging
from typing import Optional

from openai import AsyncOpenAI

from config import config

logger = logging.getLogger(__name__)


class ImageGenerationError(Exception):
    pass


class ImageProvider:
    def __init__(self):
        self._client: AsyncOpenAI | None = None

    def _get_client(self) -> AsyncOpenAI:
        if self._client is None:
            self._client = AsyncOpenAI(api_key=config.openai_api_key)
        return self._client

    async def generate_image(
        self,
        prompt: str,
        size: str = "1024x1024",
        seed: Optional[int] = None,
        quality: str = "standard",
    ) -> bytes:
        """Returns raw image bytes."""
        oai_quality = "high" if quality == "hd" else "medium"
        model = config.image_model  # gpt-image-1.5 or gpt-image-1-mini

        last_error: Exception = Exception("unknown")
        for attempt in range(config.retries + 1):
            try:
                resp = await self._get_client().images.generate(
                    model=model,
                    prompt=prompt,
                    n=1,
                    size=size,
                    quality=oai_quality,
                    output_format="png",
                )
                item = resp.data[0]
                if item.b64_json:
                    return base64.b64decode(item.b64_json)
                # fallback: download from url
                import httpx
                async with httpx.AsyncClient(timeout=60) as hc:
                    r = await hc.get(item.url)
                    r.raise_for_status()
                    return r.content
            except Exception as e:
                last_error = e
                logger.warning("OpenAI image error attempt %d/%d: %s", attempt + 1, config.retries + 1, e)
                if attempt < config.retries:
                    await asyncio.sleep(2 ** attempt)

        raise ImageGenerationError(f"Failed after {config.retries + 1} attempts: {last_error}") from last_error


image_provider = ImageProvider()

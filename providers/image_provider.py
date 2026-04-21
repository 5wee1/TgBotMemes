"""
Image provider — fal.ai Flux Schnell.
Generates image without caption text; text is overlaid via Pillow.
Swap this file to change the backend.
"""
import asyncio
import logging
from typing import Optional

import httpx

from config import config

logger = logging.getLogger(__name__)

FAL_URL = "https://fal.run/fal-ai/flux/schnell"


class ImageGenerationError(Exception):
    pass


class ImageProvider:
    def __init__(self):
        self.api_key = config.image_api_key
        self.timeout = config.timeout_seconds
        self.retries = config.retries

    async def generate_image(
        self,
        prompt: str,
        size: str = "square_hd",
        seed: Optional[int] = None,
        quality: str = "standard",
    ) -> str:
        """Returns URL of the generated image."""
        payload: dict = {
            "prompt": prompt,
            "negative_prompt": (
                "text, words, letters, numbers, watermark, signature, caption, "
                "typography, font, label, title, subtitle, writing, inscription, "
                "speech bubble, dialog, headline, any readable characters"
            ),
            "image_size": "square_hd",
            "num_inference_steps": 12 if quality == "hd" else 8,
            "enable_safety_checker": True,
        }
        if seed is not None:
            payload["seed"] = seed

        headers = {
            "Authorization": f"Key {self.api_key}",
            "Content-Type": "application/json",
        }

        last_error: Exception = Exception("unknown")
        for attempt in range(self.retries + 1):
            try:
                async with httpx.AsyncClient(timeout=self.timeout) as client:
                    resp = await client.post(FAL_URL, json=payload, headers=headers)
                    resp.raise_for_status()
                    data = resp.json()
                    images = data.get("images", [])
                    if not images:
                        raise ImageGenerationError("Empty images list from fal.ai")
                    return images[0]["url"]
            except httpx.HTTPStatusError as e:
                last_error = e
                logger.warning("fal.ai HTTP %s attempt %d/%d", e.response.status_code, attempt + 1, self.retries + 1)
                if e.response.status_code in (400, 401, 403):
                    break
            except Exception as e:
                last_error = e
                logger.warning("fal.ai error attempt %d/%d: %s", attempt + 1, self.retries + 1, e)

            if attempt < self.retries:
                await asyncio.sleep(2 ** attempt)

        raise ImageGenerationError(f"Failed after {self.retries + 1} attempts: {last_error}") from last_error


image_provider = ImageProvider()

import os
from dataclasses import dataclass, field
from dotenv import load_dotenv

load_dotenv()


@dataclass
class Config:
    bot_token: str = field(default_factory=lambda: os.environ["BOT_TOKEN"])
    image_api_base_url: str = field(default_factory=lambda: os.environ["IMAGE_API_BASE_URL"])
    image_api_key: str = field(default_factory=lambda: os.environ["IMAGE_API_KEY"])
    image_model: str = field(default_factory=lambda: os.getenv("IMAGE_MODEL", "dall-e-3"))
    timeout_seconds: int = field(default_factory=lambda: int(os.getenv("TIMEOUT_SECONDS", "90")))
    retries: int = field(default_factory=lambda: int(os.getenv("RETRIES", "2")))
    admin_ids: list[int] = field(default_factory=lambda: [
        int(x.strip()) for x in os.getenv("ADMIN_IDS", "").split(",") if x.strip()
    ])
    db_path: str = field(default_factory=lambda: os.getenv("DB_PATH", "memes.db"))
    free_daily_limit: int = field(default_factory=lambda: int(os.getenv("FREE_DAILY_LIMIT", "3")))
    rate_limit_seconds: int = field(default_factory=lambda: int(os.getenv("RATE_LIMIT_SECONDS", "10")))
    max_concurrent_per_user: int = field(default_factory=lambda: int(os.getenv("MAX_CONCURRENT_PER_USER", "2")))
    payment_provider_token: str = field(default_factory=lambda: os.getenv("PAYMENT_PROVIDER_TOKEN", ""))


config = Config()

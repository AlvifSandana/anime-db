from functools import lru_cache
from typing import List, Optional
from pydantic import BaseModel
from dotenv import load_dotenv
import os
import re


load_dotenv()


def _default_user_agents() -> List[str]:
    return [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 13_6) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.3 Safari/605.1.15",
        "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:131.0) Gecko/20100101 Firefox/131.0",
        "Mozilla/5.0 (iPhone; CPU iPhone OS 17_2 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Mobile/15E148 Safari/604.1",
        "Mozilla/5.0 (Linux; Android 14; Pixel 7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Mobile Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:131.0) Gecko/20100101 Firefox/131.0",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 13_6_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36",
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Linux; Android 14; SM-S908E) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Mobile Safari/537.36",
        "Mozilla/5.0 (iPad; CPU OS 17_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Mobile/15E148 Safari/604.1",
    ]


class Settings(BaseModel):
    app_name: str = os.getenv("APP_NAME", "anime-db")
    api_version: str = "0.1.0"
    base_url: str = os.getenv("BASE_URL", "https://otakudesu.best")
    list_path: str = os.getenv("LIST_PATH", "/anime-list/")
    http_timeout: float = float(os.getenv("HTTP_TIMEOUT", 20))
    http_connect_timeout: float = float(os.getenv("HTTP_CONNECT_TIMEOUT", 10))
    scraper_delay_min: float = float(os.getenv("SCRAPER_DELAY_MIN", 0.5))
    scraper_delay_max: float = float(os.getenv("SCRAPER_DELAY_MAX", 1.5))
    user_agent: str = os.getenv("USER_AGENT", "anime-db-scraper/0.1 (+https://example.com/contact)")
    user_agents: List[str] = (
        [ua.strip() for ua in re.split(r"[;,]", os.getenv("USER_AGENTS", "")) if ua.strip()]
        or _default_user_agents()
    )
    db_url: str = os.getenv("DB_URL", "sqlite:///./data/anime.db")
    _scraper_max_items_raw: Optional[str] = os.getenv("SCRAPER_MAX_ITEMS")
    scraper_max_items: Optional[int] = (
        int(_scraper_max_items_raw) if _scraper_max_items_raw else None
    )
    scraper_fetch_mirrors: bool = os.getenv("SCRAPER_FETCH_MIRRORS", "true").lower() == "true"
    scraper_episode_concurrency: int = int(os.getenv("SCRAPER_EPISODE_CONCURRENCY", 2))
    scraper_mirror_concurrency: int = int(os.getenv("SCRAPER_MIRROR_CONCURRENCY", 2))
    scraper_ajax_delay_min: float = float(os.getenv("SCRAPER_AJAX_DELAY_MIN", 0.3))
    scraper_ajax_delay_max: float = float(os.getenv("SCRAPER_AJAX_DELAY_MAX", 1.0))
    scraper_ajax_max_retries: int = int(os.getenv("SCRAPER_AJAX_MAX_RETRIES", 2))
    ajax_action_nonce: str = os.getenv("AJAX_ACTION_NONCE", "aa1208d27f29ca340c92c66d1926f13f")
    ajax_action_embed: str = os.getenv("AJAX_ACTION_EMBED", "2a3505c93b0035d3f455df82bf976b84")


@lru_cache
def get_settings() -> Settings:
    return Settings()

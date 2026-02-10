import asyncio
import random
from typing import Any

import httpx
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

from app.core.config import get_settings


settings = get_settings()


class ScraperClient:
    def __init__(self) -> None:
        self.client = httpx.AsyncClient(
            timeout=httpx.Timeout(settings.http_timeout, connect=settings.http_connect_timeout),
            follow_redirects=True,
        )

    async def close(self) -> None:
        await self.client.aclose()

    def _pick_user_agent(self) -> str:
        return random.choice(settings.user_agents or [settings.user_agent])

    @retry(
        reraise=True,
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=5),
        retry=retry_if_exception_type(httpx.HTTPError),
    )
    async def get(self, url: str) -> httpx.Response:
        await asyncio.sleep(random.uniform(settings.scraper_delay_min, settings.scraper_delay_max))
        headers = {"User-Agent": self._pick_user_agent()}
        resp = await self.client.get(url, headers=headers)
        resp.raise_for_status()
        return resp

    @retry(
        reraise=True,
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=5),
        retry=retry_if_exception_type(httpx.HTTPError),
    )
    async def post_form(self, url: str, data: dict, referer: str | None = None) -> httpx.Response:
        await asyncio.sleep(random.uniform(settings.scraper_ajax_delay_min, settings.scraper_ajax_delay_max))
        headers = {
            "User-Agent": self._pick_user_agent(),
            "Content-Type": "application/x-www-form-urlencoded",
            "X-Requested-With": "XMLHttpRequest",
        }
        if referer:
            headers["Referer"] = referer
            headers["Origin"] = settings.base_url
        resp = await self.client.post(url, data=data, headers=headers)
        resp.raise_for_status()
        return resp

    async def __aenter__(self) -> "ScraperClient":
        return self

    async def __aexit__(self, exc_type: Any, exc: Any, tb: Any) -> None:
        await self.close()

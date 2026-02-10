import asyncio
import logging
from datetime import datetime
from urllib.parse import urljoin
from typing import List, Optional

from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.db import models
from app.db.repository import (
    upsert_anime,
    sync_anime_genres,
    upsert_episodes,
    upsert_episode_mirror,
)
from app.db.session import SessionLocal, engine
from app.scraper.client import ScraperClient
from app.scraper.parsers import (
    parse_anime_list,
    parse_detail,
    parse_episodes,
    parse_mirrors,
    decode_embed_base64_to_iframe_src,
)


async def fetch_nonce(client: ScraperClient, referer: str) -> Optional[str]:
    data = {"action": settings.ajax_action_nonce}
    try:
        resp = await client.post_form(urljoin(settings.base_url, "/wp-admin/admin-ajax.php"), data=data, referer=referer)
        return resp.json().get("data")
    except Exception as exc:  # noqa: BLE001
        logger.warning("nonce fetch failed", extra={"error": str(exc), "referer": referer})
        return None


async def fetch_mirror_embed(client: ScraperClient, referer: str, payload: dict, nonce: str) -> Optional[str]:
    data = {
        "id": payload["mirror_id"],
        "i": payload["mirror_i"],
        "q": payload["mirror_q"],
        "nonce": nonce,
        "action": settings.ajax_action_embed,
    }
    try:
        resp = await client.post_form(urljoin(settings.base_url, "/wp-admin/admin-ajax.php"), data=data, referer=referer)
        return resp.json().get("data")
    except Exception as exc:  # noqa: BLE001
        logger.warning("mirror embed fetch failed", extra={"error": str(exc), "referer": referer, "payload": data})
        return None


async def scrape_episode_mirrors(session: Session, client: ScraperClient, episodes: List[dict]) -> None:
    for ep in episodes:
        episode_url = ep.get("episode_url")
        if not episode_url:
            continue
        try:
            ep_resp = await client.get(episode_url)
        except Exception as exc:  # noqa: BLE001
            logger.warning("failed fetching episode page for mirrors", extra={"episode_url": episode_url, "error": str(exc)})
            continue

        mirrors = parse_mirrors(ep_resp.text)
        if not mirrors:
            continue
        nonce = await fetch_nonce(client, episode_url)
        for mirror in mirrors:
            status = "failed"
            iframe_src: Optional[str] = None
            raw_embed_html: Optional[str] = None
            used_nonce: Optional[str] = nonce

            def persist(status_value: str, error_message: Optional[str] = None):
                mirror_data = {
                    **mirror,
                    "iframe_src": iframe_src,
                    "raw_embed_html": raw_embed_html,
                    "nonce": used_nonce,
                    "fetch_status": status_value,
                    "error_message": error_message,
                    "last_scraped_at": datetime.utcnow(),
                }
                upsert_episode_mirror(session, ep["anime_id"], mirror_data)

            if nonce:
                embed_b64 = await fetch_mirror_embed(client, episode_url, mirror, nonce)
                if embed_b64:
                    iframe_src = decode_embed_base64_to_iframe_src(embed_b64)
                    raw_embed_html = embed_b64
                    status = "success" if iframe_src else "partial"
                    persist(status)
                    continue

            # Retry with fresh nonce once
            nonce_retry = await fetch_nonce(client, episode_url)
            used_nonce = nonce_retry
            if nonce_retry:
                embed_b64 = await fetch_mirror_embed(client, episode_url, mirror, nonce_retry)
                if embed_b64:
                    iframe_src = decode_embed_base64_to_iframe_src(embed_b64)
                    raw_embed_html = embed_b64
                    status = "success" if iframe_src else "partial"
                    persist(status)
                    continue

            persist(status, error_message="failed to fetch mirror")
        session.commit()


logger = logging.getLogger(__name__)


settings = get_settings()


def init_db() -> None:
    models.Base.metadata.create_all(bind=engine)


async def scrape_once() -> None:
    init_db()
    async with ScraperClient() as client:
        list_url = urljoin(settings.base_url, settings.list_path)
        resp = await client.get(list_url)
        list_items = parse_anime_list(resp.text)
        if settings.scraper_max_items:
            list_items = list_items[: settings.scraper_max_items]
        logger.info("fetched list page", extra={"count": len(list_items)})

        with SessionLocal() as session:
            for item in list_items:
                logger.info("processing anime", extra={"url": item["href"], "title": item["title"]})
                anime_data = {
                    "source_url": item["href"],
                    "title": item["title"],
                    "status_list_page": item["status"],
                    "last_scraped_at": datetime.utcnow(),
                }
                anime = upsert_anime(session, anime_data)
                session.flush()
                # Fetch detail page
                detail_resp = await client.get(item["href"])
                detail_data, genres, synopsis = parse_detail(detail_resp.text)
                for k, v in detail_data.items():
                    setattr(anime, k, v)
                anime.synopsis = synopsis  # type: ignore[assignment]
                anime.last_scraped_at = datetime.utcnow()  # type: ignore[assignment]
                sync_anime_genres(session, anime, genres)
                session.flush()

                # Episodes
                episodes = parse_episodes(detail_resp.text)
                for ep in episodes:
                    ep["anime_id"] = anime.id
                upsert_episodes(session, anime, episodes)

                session.commit()
                logger.info("committed anime", extra={"url": item["href"], "episodes": len(episodes)})

                # Mirror scraping (per episode detail pages)
                if settings.scraper_fetch_mirrors:
                    await scrape_episode_mirrors(session, client, episodes)


def run_blocking_scrape() -> None:
    if not logging.getLogger().hasHandlers():
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s %(levelname)s %(name)s %(message)s",
        )
    logger.info("starting scrape run")
    asyncio.run(scrape_once())
    logger.info("scrape run completed")

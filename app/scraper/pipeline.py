import asyncio
import logging
from datetime import datetime
from urllib.parse import urljoin
from typing import List, Optional

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


async def fetch_nonce(client: ScraperClient, referer: str, semaphore: asyncio.Semaphore) -> Optional[str]:
    data = {"action": settings.ajax_action_nonce}
    try:
        async with semaphore:
            resp = await client.post_form(urljoin(settings.base_url, "/wp-admin/admin-ajax.php"), data=data, referer=referer)
        return resp.json().get("data")
    except Exception as exc:  # noqa: BLE001
        logger.warning("nonce fetch failed", extra={"error": str(exc), "referer": referer})
        return None


async def fetch_mirror_embed(
    client: ScraperClient, referer: str, payload: dict, nonce: str, semaphore: asyncio.Semaphore
) -> Optional[str]:
    data = {
        "id": payload["mirror_id"],
        "i": payload["mirror_i"],
        "q": payload["mirror_q"],
        "nonce": nonce,
        "action": settings.ajax_action_embed,
    }
    try:
        async with semaphore:
            resp = await client.post_form(urljoin(settings.base_url, "/wp-admin/admin-ajax.php"), data=data, referer=referer)
        return resp.json().get("data")
    except Exception as exc:  # noqa: BLE001
        logger.warning("mirror embed fetch failed", extra={"error": str(exc), "referer": referer, "payload": data})
        return None


async def fetch_episode_mirror_data(
    client: ScraperClient, episode_url: str, ajax_semaphore: asyncio.Semaphore
) -> List[dict]:
    try:
        ep_resp = await client.get(episode_url)
    except Exception as exc:  # noqa: BLE001
        logger.warning("failed fetching episode page for mirrors", extra={"episode_url": episode_url, "error": str(exc)})
        return []

    mirrors = parse_mirrors(ep_resp.text)
    if not mirrors:
        return []
    nonce = await fetch_nonce(client, episode_url, ajax_semaphore)
    results: List[dict] = []
    for mirror in mirrors:
        status = "failed"
        iframe_src: Optional[str] = None
        raw_embed_html: Optional[str] = None
        used_nonce: Optional[str] = nonce
        error_message: Optional[str] = None

        if nonce:
            embed_b64 = await fetch_mirror_embed(client, episode_url, mirror, nonce, ajax_semaphore)
            if embed_b64:
                iframe_src = decode_embed_base64_to_iframe_src(embed_b64)
                raw_embed_html = embed_b64
                status = "success" if iframe_src else "partial"

        if status == "failed":
            nonce_retry = await fetch_nonce(client, episode_url, ajax_semaphore)
            used_nonce = nonce_retry
            if nonce_retry:
                embed_b64 = await fetch_mirror_embed(client, episode_url, mirror, nonce_retry, ajax_semaphore)
                if embed_b64:
                    iframe_src = decode_embed_base64_to_iframe_src(embed_b64)
                    raw_embed_html = embed_b64
                    status = "success" if iframe_src else "partial"
        if status == "failed":
            error_message = "failed to fetch mirror"

        results.append(
            {
                **mirror,
                "iframe_src": iframe_src,
                "raw_embed_html": raw_embed_html,
                "nonce": used_nonce,
                "fetch_status": status,
                "error_message": error_message,
                "last_scraped_at": datetime.utcnow(),
            }
        )
    return results


async def scrape_episode_mirrors(
    client: ScraperClient,
    episodes: List[dict],
    episode_semaphore: asyncio.Semaphore,
    ajax_semaphore: asyncio.Semaphore,
) -> None:
    tasks: List[asyncio.Task] = []

    async def run_fetch(url: str, ep_id: int) -> tuple[int, List[dict]]:
        async with episode_semaphore:
            mirror_data = await fetch_episode_mirror_data(client, url, ajax_semaphore)
            return ep_id, mirror_data

    for ep in episodes:
        episode_url = ep.get("episode_url")
        episode_id_value = ep.get("episode_id")
        if not episode_url or episode_id_value is None:
            continue
        try:
            episode_id = int(episode_id_value)
        except (TypeError, ValueError):
            logger.warning(
                "invalid episode id",
                extra={"episode_id": episode_id_value, "episode_url": episode_url},
            )
            continue
        tasks.append(asyncio.create_task(run_fetch(episode_url, episode_id)))

    if not tasks:
        return

    results = await asyncio.gather(*tasks, return_exceptions=True)
    with SessionLocal() as session:
        try:
            for result in results:
                if isinstance(result, BaseException):
                    if isinstance(result, Exception):
                        logger.warning("mirror fetch task failed", extra={"error": str(result)})
                        continue
                    raise result
                if not isinstance(result, tuple):
                    logger.warning("mirror fetch task unexpected result", extra={"result": str(result)})
                    continue
                episode_id, mirrors = result
                for mirror_data in mirrors:
                    upsert_episode_mirror(session, episode_id, mirror_data)
            session.commit()
        except Exception as exc:  # noqa: BLE001
            session.rollback()
            logger.warning("mirror commit failed", extra={"error": str(exc)})
            raise


logger = logging.getLogger(__name__)


settings = get_settings()


def init_db() -> None:
    models.Base.metadata.create_all(bind=engine)


async def scrape_anime_item(
    item: dict,
    client: ScraperClient,
    episode_semaphore: asyncio.Semaphore,
    ajax_semaphore: asyncio.Semaphore,
) -> None:
    logger.info("processing anime", extra={"url": item["href"], "title": item["title"]})
    anime_data = {
        "source_url": item["href"],
        "title": item["title"],
        "status_list_page": item["status"],
        "last_scraped_at": datetime.utcnow(),
    }

    with SessionLocal() as session:
        anime = upsert_anime(session, anime_data)
        session.commit()
        session.refresh(anime)

    detail_resp = await client.get(item["href"])
    detail_data, genres, synopsis = parse_detail(detail_resp.text)
    episodes = parse_episodes(detail_resp.text)

    with SessionLocal() as session:
        try:
            anime = upsert_anime(session, anime_data)
            for k, v in detail_data.items():
                setattr(anime, k, v)
            anime.synopsis = synopsis  # type: ignore[assignment]
            anime.last_scraped_at = datetime.utcnow()  # type: ignore[assignment]
            sync_anime_genres(session, anime, genres)
            session.flush()

            for ep in episodes:
                ep["anime_id"] = anime.id
            episode_rows = upsert_episodes(session, anime, episodes)
            episode_ids_by_url = {row.episode_url: row.id for row in episode_rows}
            for ep in episodes:
                episode_url = ep.get("episode_url")
                if episode_url:
                    ep["episode_id"] = episode_ids_by_url.get(episode_url)

            session.commit()
            logger.info("committed anime", extra={"url": item["href"], "episodes": len(episodes)})
        except Exception as exc:  # noqa: BLE001
            session.rollback()
            logger.warning("anime commit failed", extra={"url": item["href"], "error": str(exc)})
            raise

    if settings.scraper_fetch_mirrors:
        await scrape_episode_mirrors(client, episodes, episode_semaphore, ajax_semaphore)


async def scrape_once() -> None:
    init_db()
    async with ScraperClient() as client:
        list_url = urljoin(settings.base_url, settings.list_path)
        resp = await client.get(list_url)
        list_items = parse_anime_list(resp.text)
        if settings.scraper_max_items:
            list_items = list_items[: settings.scraper_max_items]
        logger.info("fetched list page", extra={"count": len(list_items)})
        anime_semaphore = asyncio.Semaphore(settings.scraper_concurrency)
        episode_semaphore = asyncio.Semaphore(settings.scraper_episode_concurrency)
        ajax_semaphore = asyncio.Semaphore(settings.scraper_mirror_concurrency)
        tasks: List[asyncio.Task] = []

        async def run_item(anime_item: dict) -> None:
            async with anime_semaphore:
                await scrape_anime_item(anime_item, client, episode_semaphore, ajax_semaphore)

        for item in list_items:
            tasks.append(asyncio.create_task(run_item(item)))

        if tasks:
            results = await asyncio.gather(*tasks, return_exceptions=True)
            for result in results:
                if isinstance(result, BaseException):
                    if isinstance(result, Exception):
                        logger.warning("anime task failed", extra={"error": str(result)})
                        continue
                    raise result


def run_blocking_scrape() -> None:
    if not logging.getLogger().hasHandlers():
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s %(levelname)s %(name)s %(message)s",
        )
    logger.info("starting scrape run")
    asyncio.run(scrape_once())
    logger.info("scrape run completed")


if __name__ == "__main__":
    run_blocking_scrape()

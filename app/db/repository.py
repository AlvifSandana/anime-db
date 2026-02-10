from datetime import datetime
from typing import Iterable, List, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.db import models


def upsert_anime(session: Session, anime_data: dict) -> models.Anime:
    existing = session.execute(
        select(models.Anime).where(models.Anime.source_url == anime_data["source_url"])
    ).scalar_one_or_none()

    if existing:
        for k, v in anime_data.items():
            setattr(existing, k, v)
        existing.updated_at = datetime.utcnow()  # type: ignore[assignment]
        return existing

    anime = models.Anime(**anime_data)
    session.add(anime)
    return anime


def upsert_genres(session: Session, genre_names: Iterable[str]) -> List[models.Genre]:
    genres = []
    for name in genre_names:
        genre = session.execute(select(models.Genre).where(models.Genre.name == name)).scalar_one_or_none()
        if not genre:
            genre = models.Genre(name=name)
            session.add(genre)
        genres.append(genre)
    return genres


def sync_anime_genres(session: Session, anime: models.Anime, genre_names: Iterable[str]) -> None:
    genres = upsert_genres(session, genre_names)
    anime.genres = genres


def upsert_episodes(session: Session, anime: models.Anime, episodes: Iterable[dict]) -> List[models.Episode]:
    results: List[models.Episode] = []
    for data in episodes:
        existing = session.execute(
            select(models.Episode).where(models.Episode.episode_url == data["episode_url"])
        ).scalar_one_or_none()
        if existing:
            for k, v in data.items():
                setattr(existing, k, v)
            existing.updated_at = datetime.utcnow()  # type: ignore[assignment]
            results.append(existing)
            continue
        ep = models.Episode(**data)
        ep.anime = anime
        session.add(ep)
        results.append(ep)
    return results


def get_anime_list(session: Session, status: str | None, q: str | None, limit: int, offset: int) -> Tuple[List[models.Anime], int]:
    stmt = select(models.Anime)
    if status:
        stmt = stmt.where(models.Anime.status_list_page == status)
    if q:
        stmt = stmt.where(models.Anime.title.ilike(f"%{q}%"))
    items = list(session.execute(stmt.offset(offset).limit(limit)).scalars().all())
    total = len(session.execute(stmt.with_only_columns(models.Anime.id)).all())
    return items, total


def get_anime_by_id(session: Session, anime_id: int) -> models.Anime | None:
    return session.get(models.Anime, anime_id)


def get_episodes_by_anime(session: Session, anime_id: int, limit: int, offset: int, order: str) -> Tuple[List[models.Episode], int]:
    stmt = select(models.Episode).where(models.Episode.anime_id == anime_id)
    if order == "asc":
        stmt = stmt.order_by(models.Episode.episode_number.asc().nullslast())
    else:
        stmt = stmt.order_by(models.Episode.episode_number.desc().nullsfirst())
    items = list(session.execute(stmt.offset(offset).limit(limit)).scalars().all())
    total = len(session.execute(stmt.with_only_columns(models.Episode.id)).all())
    return items, total


def upsert_episode_mirror(session: Session, episode_id: int, mirror_data: dict) -> models.EpisodeMirror:
    stmt = select(models.EpisodeMirror).where(
        models.EpisodeMirror.episode_id == episode_id,
        models.EpisodeMirror.mirror_id == mirror_data["mirror_id"],
        models.EpisodeMirror.mirror_i == mirror_data["mirror_i"],
        models.EpisodeMirror.mirror_q == mirror_data["mirror_q"],
    )
    existing = session.execute(stmt).scalar_one_or_none()
    if existing:
        for k, v in mirror_data.items():
            setattr(existing, k, v)
        existing.updated_at = datetime.utcnow()  # type: ignore[assignment]
        return existing

    mirror = models.EpisodeMirror(**mirror_data, episode_id=episode_id)
    session.add(mirror)
    return mirror


def get_episode_mirrors(session: Session, episode_id: int, quality: str | None, provider: str | None, limit: int, offset: int) -> Tuple[List[models.EpisodeMirror], int]:
    stmt = select(models.EpisodeMirror).where(models.EpisodeMirror.episode_id == episode_id)
    if quality:
        stmt = stmt.where(models.EpisodeMirror.quality == quality)
    if provider:
        stmt = stmt.where(models.EpisodeMirror.provider_name == provider)
    items = list(session.execute(stmt.offset(offset).limit(limit)).scalars().all())
    total = len(session.execute(stmt.with_only_columns(models.EpisodeMirror.id)).all())
    return items, total

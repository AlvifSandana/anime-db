from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.db.session import SessionLocal
from app.db import repository
from app.schemas.anime import AnimeListResponse, AnimeBase, AnimeDetail, EpisodeListResponse, EpisodeOut
from app.schemas.mirror import EpisodeMirrorListResponse, EpisodeMirrorOut
from app.db import models


router = APIRouter(prefix="/anime", tags=["anime"])


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.get("/", response_model=AnimeListResponse)
def list_anime(
    status: str | None = Query(None, pattern="^(on-going|completed)$"),
    q: str | None = None,
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
):
    items, total = repository.get_anime_list(db, status, q, limit, offset)
    return {
        "items": [AnimeBase.from_orm(item) for item in items],
        "total": total,
    }


@router.get("/{anime_id}", response_model=AnimeDetail)
def anime_detail(anime_id: int, db: Session = Depends(get_db)):
    anime = repository.get_anime_by_id(db, anime_id)
    if not anime:
        raise HTTPException(status_code=404, detail="Anime not found")
    return AnimeDetail.model_validate(anime)


@router.get("/{anime_id}/episodes", response_model=EpisodeListResponse)
def anime_episodes(
    anime_id: int,
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    order: str = Query("asc", pattern="^(asc|desc)$"),
    db: Session = Depends(get_db),
):
    anime = repository.get_anime_by_id(db, anime_id)
    if not anime:
        raise HTTPException(status_code=404, detail="Anime not found")
    items, total = repository.get_episodes_by_anime(db, anime_id, limit, offset, order)
    return {
        "items": [EpisodeOut.from_orm(item) for item in items],
        "total": total,
    }


@router.get("/episodes/{episode_id}/mirrors", response_model=EpisodeMirrorListResponse)
def episode_mirrors(
    episode_id: int,
    quality: str | None = Query(None),
    provider: str | None = Query(None),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
):
    ep_obj = db.get(models.Episode, episode_id)
    if not ep_obj:
        raise HTTPException(status_code=404, detail="Episode not found")
    items, total = repository.get_episode_mirrors(db, episode_id, quality, provider, limit, offset)
    return {
        "items": [EpisodeMirrorOut.model_validate(item) for item in items],
        "total": total,
    }

from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from datetime import datetime

from app.db.session import Base


class Anime(Base):
    __tablename__ = "anime"

    id = Column(Integer, primary_key=True, index=True)
    source_url = Column(String, unique=True, nullable=False, index=True)
    title = Column(String, nullable=False)
    status_list_page = Column(String, nullable=False)
    title_japanese = Column(String)
    score = Column(String)
    producer = Column(String)
    type = Column(String)
    status_detail = Column(String)
    total_episode = Column(String)
    duration = Column(String)
    release_date = Column(String)
    studio = Column(String)
    image_url = Column(String)
    synopsis = Column(Text)
    last_scraped_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    genres = relationship("Genre", secondary="anime_genre", back_populates="animes")
    episodes = relationship("Episode", back_populates="anime", cascade="all, delete-orphan")


class Genre(Base):
    __tablename__ = "genre"

    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True, nullable=False)

    animes = relationship("Anime", secondary="anime_genre", back_populates="genres")


class AnimeGenre(Base):
    __tablename__ = "anime_genre"

    anime_id = Column(Integer, ForeignKey("anime.id", ondelete="CASCADE"), primary_key=True)
    genre_id = Column(Integer, ForeignKey("genre.id", ondelete="CASCADE"), primary_key=True)
    __table_args__ = (UniqueConstraint("anime_id", "genre_id", name="uq_anime_genre"),)


class Episode(Base):
    __tablename__ = "episode"

    id = Column(Integer, primary_key=True)
    anime_id = Column(Integer, ForeignKey("anime.id", ondelete="CASCADE"), nullable=False, index=True)
    episode_url = Column(String, unique=True, nullable=False)
    episode_title = Column(String, nullable=False)
    episode_date_text = Column(String)
    episode_number = Column(Integer)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    anime = relationship("Anime", back_populates="episodes")
    mirrors = relationship("EpisodeMirror", back_populates="episode", cascade="all, delete-orphan")


class EpisodeMirror(Base):
    __tablename__ = "episode_mirror"

    id = Column(Integer, primary_key=True)
    episode_id = Column(Integer, ForeignKey("episode.id", ondelete="CASCADE"), nullable=False, index=True)
    quality = Column(String, nullable=False)
    provider_name = Column(String, nullable=False)
    iframe_src = Column(String)
    mirror_id = Column(Integer, nullable=False)
    mirror_i = Column(Integer, nullable=False)
    mirror_q = Column(String, nullable=False)
    raw_data_content = Column(Text)
    nonce = Column(String)
    raw_embed_html = Column(Text)
    fetch_status = Column(String, default="unknown", nullable=False)
    error_message = Column(Text)
    last_scraped_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    __table_args__ = (
        UniqueConstraint("episode_id", "mirror_id", "mirror_i", "mirror_q", name="uq_episode_mirror_payload"),
        UniqueConstraint("episode_id", "quality", "provider_name", name="uq_episode_mirror_display"),
    )

    episode = relationship("Episode", back_populates="mirrors")

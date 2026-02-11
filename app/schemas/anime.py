from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field, field_validator


class EpisodeOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    episode_title: str
    episode_url: str
    episode_date_text: Optional[str] = None
    episode_number: Optional[int] = None


class AnimeBase(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    title: str
    status_list_page: str
    score: Optional[str] = None
    image_url: Optional[str] = None


class AnimeDetail(AnimeBase):
    source_url: str
    title_japanese: Optional[str] = None
    producer: Optional[str] = None
    type: Optional[str] = None
    status_detail: Optional[str] = None
    total_episode: Optional[str] = None
    duration: Optional[str] = None
    release_date: Optional[str] = None
    studio: Optional[str] = None
    synopsis: Optional[str] = None
    genres: List[str] = Field(default_factory=list)

    @field_validator("genres", mode="before")
    @classmethod
    def normalize_genres(cls, value):
        if value is None:
            return []
        if isinstance(value, str):
            values = [value]
        elif isinstance(value, (set, tuple)):
            values = list(value)
        elif isinstance(value, list):
            values = value
        else:
            values = [value]

        normalized: List[str] = []
        for item in values:
            if item is None:
                continue
            if hasattr(item, "name"):
                item = getattr(item, "name")
            if item is None:
                continue
            if not isinstance(item, str):
                item = str(item)
            item = item.strip()
            if not item:
                continue
            normalized.append(item)
        return normalized


class AnimeListResponse(BaseModel):
    items: List[AnimeBase]
    total: int


class EpisodeListResponse(BaseModel):
    items: List[EpisodeOut]
    total: int

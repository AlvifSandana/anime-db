from typing import List, Optional
from pydantic import BaseModel, ConfigDict
from datetime import datetime


class EpisodeMirrorOut(BaseModel):
    model_config = ConfigDict(from_attributes=True, ser_json_timedelta="iso8601")

    id: int
    quality: str
    provider_name: str
    iframe_src: Optional[str] = None
    mirror_id: int
    mirror_i: int
    mirror_q: str
    fetch_status: str
    last_scraped_at: Optional[datetime] = None


class EpisodeMirrorListResponse(BaseModel):
    items: List[EpisodeMirrorOut]
    total: int

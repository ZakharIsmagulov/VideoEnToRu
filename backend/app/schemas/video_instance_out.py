from pydantic import BaseModel, ConfigDict
from typing import List


class VideoInstanceOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    status: str


class VideoPageOut(BaseModel):
    items: List[VideoInstanceOut]
    last_id: int | None
    has_more: bool
    total: int | None = None

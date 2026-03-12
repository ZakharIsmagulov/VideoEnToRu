from pydantic import BaseModel, ConfigDict


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int


class VideoInstanceOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
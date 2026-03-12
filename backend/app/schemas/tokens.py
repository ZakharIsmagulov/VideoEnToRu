from pydantic import BaseModel


class TokenOnly(BaseModel):
    access_token: str
    token_type: str

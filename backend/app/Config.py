from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    db_url: str

    jwt_secret: str
    jwt_algo: str
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 15
    jwt_issuer: str
    jwt_audience: str
    token_url: str
    refresh_url: str
    is_secure_cookie: bool

    api_logger: str
    pipeline_logger: str

    model_config = SettingsConfigDict(
        env_file="app/.env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()
settings.is_secure_cookie = False
# if settings.is_secure_cookie == "False":
#     settings.is_secure_cookie = False
# else:
#     settings.is_secure_cookie = True

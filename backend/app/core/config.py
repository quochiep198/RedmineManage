import base64
import hashlib

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env")

    APP_NAME: str = "Redmine Simple Starter"
    DATABASE_URL: str
    SECRET_KEY: str = "change-me"
    CORS_ORIGINS: str = "http://localhost:3000"
    COOKIE_SECURE: bool = False
    REDMINE_SECRET_KEY: str = ""
    REDMINE_TIMEOUT_SECONDS: int = 10
    CLOSED_STATUS_IDS: str = "3,5"

    @property
    def cors_origins_list(self) -> list[str]:
        return [item.strip() for item in self.CORS_ORIGINS.split(",") if item.strip()]

    @property
    def redmine_fernet_key(self) -> str:
        if self.REDMINE_SECRET_KEY:
            return self.REDMINE_SECRET_KEY
        digest = hashlib.sha256(self.SECRET_KEY.encode("utf-8")).digest()
        return base64.urlsafe_b64encode(digest).decode("ascii")

    @property
    def closed_status_ids(self) -> list[int]:
        return [
            int(item.strip())
            for item in self.CLOSED_STATUS_IDS.split(",")
            if item.strip()
        ]

    def model_post_init(self, _):
        if self.SECRET_KEY == "change-me":
            raise ValueError(
                "SECRET_KEY must be set in .env — do not ship with the default 'change-me' value."
            )


settings = Settings()

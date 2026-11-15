from functools import cache

from pydantic import BaseModel

from blunder.shared.core.config import BaseSettings


class APISettings(BaseModel):
    host: str
    port: int

    @property
    def url(self) -> str:
        protocol = "https" if self.port == 443 else "http"
        return f"{protocol}://{self.host}:{self.port}"


class IngestionSettings(BaseModel):
    batch_size: int
    concurrency: int


class Settings(BaseSettings):
    api: APISettings
    ingestion: IngestionSettings


@cache
def settings() -> Settings:
    return Settings()

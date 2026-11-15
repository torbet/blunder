from functools import cache

from pydantic import BaseModel

from blunder.shared.core.config import BaseSettings


class APISettings(BaseModel):
    port: int


class PostgresSettings(BaseModel):
    host: str
    port: int
    user: str
    password: str
    database: str

    @property
    def url(self) -> str:
        return f"postgresql+asyncpg://{self.user}:{self.password}@{self.host}:{self.port}/{self.database}"


class Settings(BaseSettings):
    api: APISettings
    postgres: PostgresSettings


@cache
def settings() -> Settings:
    return Settings()

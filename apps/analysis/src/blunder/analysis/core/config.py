from functools import cache
from pathlib import Path

from pydantic import BaseModel

from blunder.shared.core.config import BaseSettings


class AnalysisSettings(BaseModel):
    registry: Path


class Settings(BaseSettings):
    analysis: AnalysisSettings


@cache
def settings() -> Settings:
    return Settings()

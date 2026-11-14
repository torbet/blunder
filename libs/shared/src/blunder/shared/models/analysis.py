from uuid import UUID

from pydantic import BaseModel

from blunder.shared.analysis import PipelineConfig
from blunder.shared.models import Identifiable, Timestamped


class AnalysisBase(BaseModel):
    config: PipelineConfig


class Analysis(Identifiable, AnalysisBase): ...


class FeatureBase(BaseModel):
    analysis_id: UUID

    evaluation: int | None = None
    best: str | None = None

    probability: float | None = None
    entropy: float | None = None
    ponder: float | None = None

    win: float | None = None
    draw: float | None = None
    loss: float | None = None


class Feature(Timestamped, FeatureBase):
    game_id: UUID
    ply: int

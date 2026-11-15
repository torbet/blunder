from uuid import UUID

from pydantic import BaseModel

from blunder.shared.analysis import PipelineConfig
from blunder.shared.models import Identifiable, Timestamped
from blunder.shared.models.game import Label


class AnalysisBase(BaseModel):
    config: PipelineConfig


class Analysis(Identifiable, AnalysisBase): ...


class StockfishFeature(BaseModel):
    evaluation: int | None = None
    best: str | None = None


class MaiaFeature(BaseModel):
    probability: float | None = None
    entropy: float | None = None
    ponder: float | None = None

    win: float | None = None
    draw: float | None = None
    loss: float | None = None


class FeatureBase(StockfishFeature, MaiaFeature):
    analysis_id: UUID


class Feature(Timestamped, FeatureBase):
    game_id: UUID
    ply: int


class MovePredictionBase(BaseModel):
    analysis_id: UUID

    cheating: float


class MovePrediction(Timestamped, MovePredictionBase):
    game_id: UUID
    ply: int


# The game labels with the name of each in a game prediction, in the order of the model's outcomes.
LABELS: dict[Label, str] = {
    (False, False): "neither",
    (True, False): "white",
    (False, True): "black",
    (True, True): "both",
}


class GamePredictionBase(BaseModel):
    analysis_id: UUID

    neither: float
    white: float
    black: float
    both: float


class GamePrediction(Timestamped, GamePredictionBase):
    game_id: UUID

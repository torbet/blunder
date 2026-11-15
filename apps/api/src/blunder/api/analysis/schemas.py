from blunder.shared.models.analysis import (
    Analysis,
    AnalysisBase,
    Feature,
    FeatureBase,
    GamePrediction,
    GamePredictionBase,
    MovePrediction,
    MovePredictionBase,
)


class AnalysisRead(Analysis): ...


class AnalysisCreate(AnalysisBase): ...


class FeatureRead(Feature): ...


class FeatureCreate(FeatureBase):
    ply: int


class MovePredictionRead(MovePrediction): ...


class MovePredictionCreate(MovePredictionBase):
    ply: int


class GamePredictionRead(GamePrediction): ...


class GamePredictionCreate(GamePredictionBase): ...

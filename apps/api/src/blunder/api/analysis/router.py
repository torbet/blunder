from uuid import UUID

from fastapi import APIRouter, HTTPException

from blunder.api.analysis.models import Analysis, Feature, GamePrediction, MovePrediction
from blunder.api.analysis.schemas import (
    AnalysisCreate,
    AnalysisRead,
    FeatureCreate,
    FeatureRead,
    GamePredictionCreate,
    GamePredictionRead,
    MovePredictionCreate,
    MovePredictionRead,
)
from blunder.api.core.dependencies import Session
from blunder.api.game.models import Game

router = APIRouter(prefix="/analyses", tags=["analyses"])


@router.post("/")
async def create_analyses(body: list[AnalysisCreate], session: Session) -> list[AnalysisRead]:
    analyses = [Analysis(**analysis.model_dump()) for analysis in body]
    session.add_all(analyses)
    await session.commit()
    return [AnalysisRead.model_validate(analysis) for analysis in analyses]


@router.post("/{game_id}/features")
async def create_features(game_id: UUID, body: list[FeatureCreate], session: Session) -> list[FeatureRead]:
    game = await session.get(Game, game_id)
    if not game:
        raise HTTPException(status_code=404, detail="Game not found")
    if not {feature.ply for feature in body} <= {move.ply for move in game.moves}:
        raise HTTPException(status_code=422, detail="Unknown ply")
    features = [Feature(game_id=game_id, **feature.model_dump()) for feature in body]
    session.add_all(features)
    await session.commit()
    return [FeatureRead.model_validate(feature) for feature in features]


@router.post("/{game_id}/move-predictions")
async def create_move_predictions(
    game_id: UUID, body: list[MovePredictionCreate], session: Session
) -> list[MovePredictionRead]:
    game = await session.get(Game, game_id)
    if not game:
        raise HTTPException(status_code=404, detail="Game not found")
    if not {prediction.ply for prediction in body} <= {move.ply for move in game.moves}:
        raise HTTPException(status_code=422, detail="Unknown ply")
    predictions = [MovePrediction(game_id=game_id, **prediction.model_dump()) for prediction in body]
    session.add_all(predictions)
    await session.commit()
    return [MovePredictionRead.model_validate(prediction) for prediction in predictions]


@router.post("/{game_id}/game-predictions")
async def create_game_predictions(
    game_id: UUID, body: list[GamePredictionCreate], session: Session
) -> list[GamePredictionRead]:
    game = await session.get(Game, game_id)
    if not game:
        raise HTTPException(status_code=404, detail="Game not found")
    predictions = [GamePrediction(game_id=game_id, **prediction.model_dump()) for prediction in body]
    session.add_all(predictions)
    await session.commit()
    return [GamePredictionRead.model_validate(prediction) for prediction in predictions]

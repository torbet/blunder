from uuid import UUID

from fastapi import APIRouter, HTTPException

from blunder.api.analysis.models import Analysis, Feature
from blunder.api.analysis.schemas import AnalysisCreate, AnalysisRead, FeatureCreate, FeatureRead
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
    features = [Feature(game_id=game_id, **feature.model_dump()) for feature in body]
    session.add_all(features)
    await session.commit()
    return [FeatureRead.model_validate(feature) for feature in features]

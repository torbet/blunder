import asyncio
from collections.abc import Iterable
from itertools import batched, groupby
from uuid import UUID

from rich import progress

from blunder.client import Client
from blunder.client.api.analyses import (
    create_analyses,
    create_features,
    create_game_predictions,
    create_move_predictions,
)
from blunder.client.api.games import create_games
from blunder.client.models import (
    AnalysisCreate,
    Control,
    Elos,
    FeatureCreate,
    GameCreate,
    GamePredictionCreate,
    MaiaConfig,
    MoveCreate,
    MovePredictionCreate,
    PipelineConfig,
    Players,
    Result,
    Source,
    StockfishConfig,
)
from blunder.ingestion.core.config import settings
from blunder.shared.core.records import AnalysisRecord, GameRecord, Record


class Ingestor:
    def __init__(self) -> None:
        self.client = Client(base_url=settings().api.url)
        self.ids: dict[UUID, UUID] = {}

    async def ingest(self, records: Iterable[Record], total: int | None = None) -> None:
        with progress.Progress() as bars:
            task = bars.add_task("Ingesting", total=total)

            async with self.client:
                for kind, group in groupby(records, lambda r: r.type):
                    batches = batched(group, settings().ingestion.batch_size)
                    for window in batched(batches, settings().ingestion.concurrency):
                        await asyncio.gather(*(self._ingest(kind, batch) for batch in window))
                        bars.advance(task, sum(map(len, window)))

    async def _ingest(self, kind: str, batch: tuple[Record, ...]) -> None:
        match kind:
            case "analysis":
                await self._ingest_analyses([r for r in batch if r.type == "analysis"])
            case "game":
                await self._ingest_games([r for r in batch if r.type == "game"])

    async def _ingest_analyses(self, records: list[AnalysisRecord]) -> None:
        analyses = await create_analyses.asyncio(
            client=self.client, body=[AnalysisCreate(config=self._config(record)) for record in records]
        )
        if not isinstance(analyses, list):
            raise TypeError("Failed to create analyses")

        for record, analysis in zip(records, analyses, strict=True):
            self.ids[record.id] = analysis.id

    async def _ingest_games(self, records: list[GameRecord]) -> None:
        games = await create_games.asyncio(
            client=self.client,
            body=[
                GameCreate(
                    source=Source(record.source),
                    key=record.key,
                    result=Result(record.result),
                    players=Players(white=record.players.white, black=record.players.black),
                    elos=Elos(white=record.elos.white, black=record.elos.black),
                    control=Control(base=record.control.base, increment=record.control.increment),
                    played=record.played,
                    moves=[MoveCreate(ply=move.ply, uci=move.uci, time=move.time) for move in record.moves],
                )
                for record in records
            ],
        )
        if not isinstance(games, list):
            raise TypeError("Failed to create games")

        for record, game in zip(records, games, strict=True):
            self.ids[record.id] = game.id

        await self._ingest_features(records)
        await self._ingest_predictions(records)

    async def _ingest_features(self, records: list[GameRecord]) -> None:
        for record in records:
            game_id = self.ids[record.id]
            body = [
                FeatureCreate(
                    analysis_id=self.ids[feature.analysis_id],
                    ply=move.ply,
                    evaluation=feature.evaluation,
                    best=feature.best,
                    probability=feature.probability,
                    entropy=feature.entropy,
                    ponder=feature.ponder,
                    win=feature.win,
                    draw=feature.draw,
                    loss=feature.loss,
                )
                for move in record.moves
                for feature in move.features
            ]
            if not body:
                continue

            features = await create_features.asyncio(client=self.client, game_id=game_id, body=body)
            if not isinstance(features, list):
                raise TypeError("Failed to create features")

    async def _ingest_predictions(self, records: list[GameRecord]) -> None:
        for record in records:
            game_id = self.ids[record.id]
            moves = [
                MovePredictionCreate(
                    analysis_id=self.ids[prediction.analysis_id], ply=move.ply, cheating=prediction.cheating
                )
                for move in record.moves
                for prediction in move.predictions
            ]
            games = [
                GamePredictionCreate(
                    analysis_id=self.ids[prediction.analysis_id],
                    neither=prediction.neither,
                    white=prediction.white,
                    black=prediction.black,
                    both=prediction.both,
                )
                for prediction in record.predictions
            ]

            if moves:
                result = await create_move_predictions.asyncio(client=self.client, game_id=game_id, body=moves)
                if not isinstance(result, list):
                    raise TypeError("Failed to create move predictions")

            if games:
                result = await create_game_predictions.asyncio(client=self.client, game_id=game_id, body=games)
                if not isinstance(result, list):
                    raise TypeError("Failed to create game predictions")

    @staticmethod
    def _config(record: AnalysisRecord) -> PipelineConfig:
        steps = []
        for step in record.config.steps:
            match step.type:
                case "stockfish":
                    steps.append(StockfishConfig(depth=step.depth))
                case "maia":
                    steps.append(MaiaConfig(model=step.model, batch=step.batch))
        return PipelineConfig(chunk=record.config.chunk, steps=steps)

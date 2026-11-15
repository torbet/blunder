from collections.abc import AsyncIterable, Iterator
from pathlib import Path
from typing import Annotated, Literal
from uuid import UUID, uuid4

import chess
from pydantic import BaseModel, Field, TypeAdapter

from blunder.shared.models.analysis import AnalysisBase, FeatureBase, GamePredictionBase, MovePredictionBase
from blunder.shared.models.game import Color, GameBase, Label, MoveBase


class RecordBase(BaseModel):
    id: UUID = Field(default_factory=uuid4)


class AnalysisRecord(RecordBase, AnalysisBase):
    type: Literal["analysis"] = "analysis"


class MoveRecord(MoveBase):
    label: bool | None = None
    features: list[FeatureBase] = Field(default_factory=list)
    predictions: list[MovePredictionBase] = Field(default_factory=list)

    @property
    def color(self) -> Color:
        return "black" if self.ply % 2 else "white"


class GameRecord(RecordBase, GameBase):
    type: Literal["game"] = "game"
    moves: list[MoveRecord]
    predictions: list[GamePredictionBase] = Field(default_factory=list)

    @property
    def label(self) -> Label | None:
        if any(move.label is None for move in self.moves):
            return None
        cheaters = {move.color for move in self.moves if move.label}
        return "white" in cheaters, "black" in cheaters

    def positions(self) -> Iterator[chess.Board]:
        board = chess.Board()
        yield board.copy()

        for move in self.moves:
            board.push_uci(move.uci)
            yield board.copy()


type Record = Annotated[GameRecord | AnalysisRecord, Field(discriminator="type")]


class Records:
    adapter = TypeAdapter(Record)

    @classmethod
    def load(cls, path: Path) -> Iterator[Record]:
        with path.open() as f:
            for line in f:
                yield cls.adapter.validate_json(line)

    @staticmethod
    async def save(records: AsyncIterable[Record], path: Path) -> None:
        with path.open("w") as f:
            async for record in records:
                f.write(record.model_dump_json() + "\n")

    @staticmethod
    def count(path: Path) -> int:
        with path.open("rb") as f:
            return sum(1 for _ in f)

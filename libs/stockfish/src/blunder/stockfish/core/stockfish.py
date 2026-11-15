import asyncio
import os
from collections.abc import AsyncGenerator, Sequence
from contextlib import asynccontextmanager
from itertools import chain, pairwise
from typing import NamedTuple

import chess.engine

from blunder.shared.core.records import GameRecord, MoveRecord
from blunder.shared.models.analysis import StockfishFeature

MATE = 10000


class Regret(NamedTuple):
    best: str
    loss: int


class Stockfish:
    def __init__(self, depth: int) -> None:
        self.limit = chess.engine.Limit(depth=depth)
        self.idle: asyncio.Queue[chess.engine.UciProtocol] = asyncio.Queue()

    @asynccontextmanager
    async def open(self) -> AsyncGenerator[None]:
        popen = await asyncio.gather(*(chess.engine.popen_uci("stockfish") for _ in range(os.process_cpu_count() or 1)))
        engines = [engine for _, engine in popen]

        for engine in engines:
            self.idle.put_nowait(engine)

        try:
            yield
        finally:
            await asyncio.gather(*(engine.quit() for engine in engines))

    @asynccontextmanager
    async def _engine(self) -> AsyncGenerator[chess.engine.UciProtocol]:
        engine = await self.idle.get()

        try:
            yield engine
        finally:
            self.idle.put_nowait(engine)

    async def features(self, games: Sequence[GameRecord]) -> list[StockfishFeature]:
        """The features of every move played in the games."""
        return list(chain.from_iterable(await asyncio.gather(*map(self._analyse, games))))

    async def _analyse(self, game: GameRecord) -> list[StockfishFeature]:
        async with self._engine() as engine:
            infos = [await engine.analyse(board, self.limit, game=game.id) for board in game.positions()]

        return [
            StockfishFeature(evaluation=after["score"].white().score(mate_score=MATE), best=before["pv"][0].uci())
            for before, after in pairwise(infos)
        ]

    async def regret(self, boards: Sequence[chess.Board], moves: Sequence[MoveRecord]) -> list[Regret]:
        """The engine's choice in each position, and the centipawns a candidate move gives up against it."""
        return await asyncio.gather(*map(self._regret, boards, moves))

    async def _regret(self, board: chess.Board, move: MoveRecord) -> Regret:
        async with self._engine() as engine:
            best = await engine.analyse(board, self.limit, game=board.fen())
            uci = best["pv"][0].uci()
            played = best

            if move.uci != uci:
                root = [chess.Move.from_uci(move.uci)]
                played = await engine.analyse(board, self.limit, root_moves=root, game=board.fen())

        best_score, played_score = (info["score"].relative.score(mate_score=MATE) for info in (best, played))
        return Regret(uci, best_score - played_score)

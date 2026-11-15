from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from blunder.analysis.core.pipeline import PipelineContext, PipelineStep
from blunder.shared.analysis.stockfish import StockfishConfig
from blunder.stockfish.core.stockfish import Stockfish


class StockfishStep(PipelineStep):
    def __init__(self, config: StockfishConfig) -> None:
        self.stockfish = Stockfish(config.depth)

    @asynccontextmanager
    async def open(self) -> AsyncGenerator[None]:
        async with self.stockfish.open():
            yield

    async def run(self, ctx: PipelineContext) -> None:
        ctx.merge(await self.stockfish.features(ctx.games))

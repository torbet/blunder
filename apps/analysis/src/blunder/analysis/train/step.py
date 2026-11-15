from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from rich import print

from blunder.analysis.core.pipeline import PipelineContext, PipelineStep
from blunder.analysis.core.registry import Registry
from blunder.analysis.train.trainer import Trainer
from blunder.shared.analysis.train import TrainConfig


class TrainStep(PipelineStep):
    def __init__(self, config: TrainConfig) -> None:
        self.trainer = Trainer(config)

    @asynccontextmanager
    async def open(self) -> AsyncGenerator[None]:
        yield
        # Training needs every chunk, so it starts once the pipeline has run to the end.
        manifest, weights = self.trainer.fit()
        print(f"Saved version {Registry.create().save(manifest, weights)}: {manifest.test}")

    async def run(self, ctx: PipelineContext) -> None:
        for game in ctx.games:
            self.trainer.add(game)

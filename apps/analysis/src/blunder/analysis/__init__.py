import asyncio
from pathlib import Path

import typer

from blunder.analysis.core.pipeline import Pipeline
from blunder.analysis.core.sampler import Sampler
from blunder.shared.analysis import PipelineConfig
from blunder.shared.core.records import Records


def analyse() -> None:
    def _command(config: Path, input: Path, output: Path) -> None:
        pipeline = Pipeline.build(PipelineConfig.load(config))
        records = pipeline.run(Records.load(input), total=Records.count(input))
        asyncio.run(Records.save(records, output))

    typer.run(_command)


def sample() -> None:
    def _command(input: Path, output: Path, limit: int = 10_000) -> None:
        asyncio.run(Records.save(Sampler(limit).sample(input), output))

    typer.run(_command)

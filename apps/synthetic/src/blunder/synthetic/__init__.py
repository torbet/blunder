import asyncio
from pathlib import Path

import typer

from blunder.shared.core.records import Records
from blunder.synthetic.core.config import SyntheticConfig
from blunder.synthetic.core.generator import Generator


def generate() -> None:
    def _command(config: Path, output: Path, limit: int = 10_000) -> None:
        generator = Generator(SyntheticConfig.load(config))
        asyncio.run(Records.save(generator.generate(limit), output))

    typer.run(_command)

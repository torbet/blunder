from pathlib import Path

import yaml
from pydantic import BaseModel

from blunder.shared.models.game import Control


class Style(BaseModel):
    """Consults Stockfish in positions at least `entropy` complex, and plays its move if Maia's costs `regret` cp."""

    name: str
    regret: int
    entropy: float


class Ratings(BaseModel):
    """Each game's Elo is drawn around `mean` by `deviation`, and each side strays from it by `gap`."""

    mean: int
    deviation: int
    gap: int


class SyntheticConfig(BaseModel):
    seed: int
    model: str
    batch: int
    depth: int
    elos: Ratings
    controls: list[Control]
    styles: list[Style]

    @classmethod
    def load(cls, path: Path) -> SyntheticConfig:
        with path.open() as file:
            return cls.model_validate(yaml.safe_load(file))

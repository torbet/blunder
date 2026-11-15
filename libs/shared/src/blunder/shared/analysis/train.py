from typing import Literal

from pydantic import BaseModel


class ModelConfig(BaseModel):
    dim: int
    layers: int
    heads: int


class TrainConfig(BaseModel):
    type: Literal["train"] = "train"

    epochs: int
    batch: int
    lr: float
    seed: int

    model: ModelConfig

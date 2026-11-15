from typing import Literal

from pydantic import BaseModel


class PredictConfig(BaseModel):
    type: Literal["predict"] = "predict"

    version: int

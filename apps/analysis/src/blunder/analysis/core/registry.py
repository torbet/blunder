from abc import ABC, abstractmethod
from pathlib import Path

from pydantic import BaseModel
from safetensors.torch import load_file, save_file
from torch import Tensor

from blunder.analysis.core.config import settings
from blunder.shared.analysis.train import TrainConfig


class Metrics(BaseModel):
    loss: float
    accuracy: float
    auc: float


class Manifest(BaseModel):
    config: TrainConfig
    val: Metrics
    test: Metrics


class Registry(ABC):
    """The versions of one model, numbered from 1."""

    @abstractmethod
    def latest(self) -> int: ...

    @abstractmethod
    def save(self, manifest: Manifest, weights: dict[str, Tensor]) -> int:
        """Store a model as the next version and return it."""

    @abstractmethod
    def load(self, version: int) -> tuple[Manifest, dict[str, Tensor]]: ...

    @classmethod
    def create(cls) -> Registry:
        return LocalRegistry(settings().analysis.registry)


class LocalRegistry(Registry):
    def __init__(self, root: Path) -> None:
        self.root = root

    def latest(self) -> int:
        return max((int(path.name) for path in self.root.glob("*") if path.name.isdigit()), default=0)

    def save(self, manifest: Manifest, weights: dict[str, Tensor]) -> int:
        version = self.latest() + 1
        staging = self.root / f".{version}"
        staging.mkdir(parents=True)
        save_file(weights, staging / "weights.safetensors")
        (staging / "manifest.json").write_text(manifest.model_dump_json(indent=2))
        staging.rename(self.root / str(version))
        return version

    def load(self, version: int) -> tuple[Manifest, dict[str, Tensor]]:
        path = self.root / str(version)
        manifest = Manifest.model_validate_json((path / "manifest.json").read_text())
        return manifest, load_file(path / "weights.safetensors")

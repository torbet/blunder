import math
import zlib
from collections.abc import Sequence
from itertools import batched

import torch
import torch.nn.functional as F
from rich import print
from torch import Tensor, nn

from blunder.analysis.core.model import DEVICE, Detector
from blunder.analysis.core.registry import Manifest, Metrics
from blunder.shared.analysis.train import TrainConfig
from blunder.shared.core.records import GameRecord
from blunder.shared.models.analysis import LABELS

type Sample = tuple[Tensor, Tensor, Tensor]
type Outputs = tuple[Tensor, Tensor, Tensor, Tensor]

# Games fall into ten buckets by hash: eight train, one validation and one test.
SPLITS = ["train"] * 8 + ["val", "test"]


class Trainer:
    """Trains on encoded games, each assigned by hash to the train, validation or test split."""

    def __init__(self, config: TrainConfig) -> None:
        self.config = config
        self.splits: dict[str, list[Sample]] = {split: [] for split in SPLITS}

    def add(self, game: GameRecord) -> None:
        if (label := game.label) is None:
            return

        split = SPLITS[zlib.crc32(f"{game.source}:{game.key}".encode()) % len(SPLITS)]
        moves = torch.tensor([move.label for move in game.moves], dtype=torch.float)
        self.splits[split].append((Detector.encode(game), moves, torch.tensor(list(LABELS).index(label))))

    def fit(self) -> tuple[Manifest, dict[str, Tensor]]:
        config, games = self.config, self.splits["train"]
        torch.manual_seed(config.seed)

        model = Detector(config.model).to(DEVICE)
        optimiser = torch.optim.AdamW(model.parameters(), lr=config.lr, weight_decay=0.01)
        schedule = torch.optim.lr_scheduler.OneCycleLR(
            optimiser, max_lr=config.lr, total_steps=config.epochs * math.ceil(len(games) / config.batch), pct_start=0.1
        )

        for epoch in range(config.epochs):
            model.train()
            for batch in batched((games[i] for i in torch.randperm(len(games)).tolist()), config.batch):
                optimiser.zero_grad()
                self.loss(*self.forward(model, batch)).backward()
                nn.utils.clip_grad_norm_(model.parameters(), 1.0)
                optimiser.step()
                schedule.step()

            val = self.evaluate(model, "val")
            print(f"Epoch {epoch + 1}/{config.epochs}: {val}")

        manifest = Manifest(config=config, val=val, test=self.evaluate(model, "test"))
        return manifest, model.state_dict()

    @staticmethod
    def forward(model: Detector, batch: Sequence[Sample]) -> Outputs:
        tokens, moves, games = zip(*batch, strict=True)
        return *model(tokens), torch.cat(moves).to(DEVICE), torch.stack(games).to(DEVICE)

    @staticmethod
    def loss(move_logits: Tensor, game_logits: Tensor, moves: Tensor, games: Tensor) -> Tensor:
        return F.binary_cross_entropy_with_logits(move_logits, moves) + F.cross_entropy(game_logits, games)

    @torch.inference_mode()
    def evaluate(self, model: Detector, split: str) -> Metrics:
        model.eval()
        outputs = [self.forward(model, batch) for batch in batched(self.splits[split], self.config.batch)]
        move_logits, game_logits, moves, games = (torch.cat(output) for output in zip(*outputs, strict=True))

        loss = self.loss(move_logits, game_logits, moves, games).item()
        accuracy = (game_logits.argmax(-1) == games).float().mean().item()
        return Metrics(loss=round(loss, 4), accuracy=round(accuracy, 4), auc=round(self.auc(move_logits, moves), 4))

    @staticmethod
    def auc(scores: Tensor, labels: Tensor) -> float:
        """The chance a cheating move outscores a fair one, from the rank sum of the cheating moves."""
        positives = labels == 1
        n = positives.sum()
        ranks = scores.argsort().argsort()[positives].sum()
        return ((ranks - n * (n - 1) / 2) / (n * (len(labels) - n))).item()

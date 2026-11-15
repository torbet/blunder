import math
from collections.abc import Sequence

import torch
from torch import Tensor, nn
from torch.nn.utils.rnn import pad_sequence

from blunder.shared.analysis.train import ModelConfig
from blunder.shared.core.records import GameRecord
from blunder.shared.models.analysis import LABELS

DEVICE = torch.accelerator.current_accelerator() or torch.device("cpu")
TOKENS = 13
REACH = 64


class Detector(nn.Module):
    """Transformer over the plies of a game that flags engine-assisted moves and sides.

    Modelled on Maia3: pre-norm blocks and one learned attention bias, shared by every layer and indexed by the signed
    distance between plies, whose parity separates a side's own moves from its opponent's.
    """

    def __init__(self, config: ModelConfig) -> None:
        super().__init__()
        dim, heads = config.dim, config.heads
        self.tokens = nn.Linear(TOKENS, dim)
        self.side = nn.Embedding(2, dim)
        self.bias = nn.Embedding(2 * REACH + 1, heads)
        layer = nn.TransformerEncoderLayer(
            dim, heads, 2 * dim, dropout=0.0, activation="gelu", batch_first=True, norm_first=True
        )
        self.encoder = nn.TransformerEncoder(layer, config.layers, norm=nn.LayerNorm(dim), enable_nested_tensor=False)
        self.move_head = nn.Sequential(nn.Linear(dim, dim), nn.GELU(), nn.Linear(dim, 1))
        self.game_head = nn.Sequential(nn.Flatten(1), nn.Linear(2 * dim, dim), nn.GELU(), nn.Linear(dim, len(LABELS)))

    @staticmethod
    def encode(game: GameRecord) -> Tensor:
        """Encode a game as one token per ply, from the point of view of the side that moved."""

        def winning(centipawns: float) -> float:
            return 1 / (1 + math.exp(-centipawns / 400))

        before = 0.0  # evaluation (from white's view) ahead of the first ply is unknown, so treated as level
        tokens = []

        for move in game.moves:
            feature = move.features[-1]
            sign = 1 if move.color == "white" else -1
            after = float(feature.evaluation or 0)
            played = max(feature.probability or 0.0, 1e-6)
            outlook = (feature.win or 0.0) + 0.5 * (feature.draw or 0.0)
            seconds = move.time or 0.0
            predicted = feature.ponder or 0.0
            tokens.append(
                [
                    float(move.uci == feature.best),
                    max(winning(sign * before) - winning(sign * after), 0.0),
                    math.log1p(max(sign * (before - after), 0.0)),
                    math.log(played),
                    played,
                    feature.entropy or 0.0,
                    outlook if sign > 0 else 1 - outlook,
                    math.log1p(seconds),
                    math.log1p(predicted),
                    math.log((seconds + 0.1) / (predicted + 0.1)) if move.time is not None else 0.0,
                    float(move.time is not None),
                    winning(sign * after),
                    float(move.ply),
                ]
            )
            before = after

        return torch.tensor(tokens)

    def forward(self, tokens: Sequence[Tensor]) -> tuple[Tensor, Tensor]:
        """Return a cheating logit per ply (all games concatenated) and, per game, a logit for each of LABELS."""
        device = self.side.weight.device
        x = pad_sequence(list(tokens), batch_first=True).to(device)
        games, length, _ = x.shape
        plies = torch.arange(length, device=device)
        mask = plies < torch.tensor([len(game) for game in tokens], device=device)[:, None]
        sides = plies % 2

        distance = (plies[None, :] - plies[:, None]).clamp(-REACH, REACH) + REACH
        bias = self.bias(distance).permute(2, 0, 1).expand(games, -1, -1, -1)
        bias = bias.masked_fill(~mask[:, None, None, :], torch.finfo(x.dtype).min)

        x = self.encoder(self.tokens(x) + self.side(sides), mask=bias.flatten(0, 1))
        owned = ((sides == torch.arange(2, device=device)[:, None]) & mask[:, None]).to(x.dtype)
        pooled = owned @ x / owned.sum(-1, keepdim=True).clamp(min=1)
        return self.move_head(x[mask]).squeeze(-1), self.game_head(pooled)

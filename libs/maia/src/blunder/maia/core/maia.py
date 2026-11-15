import math
from collections import deque
from collections.abc import Iterable, Iterator, Sequence
from itertools import batched, chain, islice
from types import SimpleNamespace
from typing import NamedTuple

import chess
import torch
from maia3.dataset import get_historical_tokens, tokenize_board
from maia3.model_registry import resolve_checkpoint_path, resolve_model_spec
from maia3.uci import load_model
from maia3.utils import get_all_possible_moves, mirror_move

from blunder.shared.core.records import GameRecord
from blunder.shared.models.analysis import MaiaFeature


class Input(NamedTuple):
    tokens: torch.Tensor
    white: bool
    legal: list[str]
    elos: tuple[int, int]
    played: str | None


class Maia:
    def __init__(self, model: str, batch: int) -> None:
        spec = resolve_model_spec(model)
        self.config = SimpleNamespace(
            **spec.config,
            device=str(torch.accelerator.current_accelerator() or "cpu"),
            checkpoint_path=resolve_checkpoint_path(spec),
        )
        self.model = load_model(self.config)
        self.indices = {uci: index for index, uci in enumerate(get_all_possible_moves())}
        self.batch = batch

    def features(self, games: Sequence[GameRecord]) -> list[MaiaFeature]:
        """The features of every move played in the games."""
        return self._assess(chain.from_iterable(islice(self._inputs(game), len(game.moves)) for game in games))

    def _inputs(self, game: GameRecord) -> Iterator[Input]:
        """The model input before each ply, tokenising each board once."""
        board, history = chess.Board(), deque(maxlen=self.config.history)
        white, black = game.elos.white, game.elos.black

        for ply, clock in enumerate(game.clocks()):
            history.append(tokenize_board(board))

            played = game.moves[ply].uci if ply < len(game.moves) else None

            tokens = get_historical_tokens(
                list(history),
                self.config,
                base=game.control.base,
                inc=game.control.increment,
                clk_left_before=clock,
                clk_ponder=0.0,
            )
            elos = (white, black) if board.turn else (black, white)
            yield Input(tokens, board.turn, [move.uci() for move in board.legal_moves], elos, played)

            if played:
                board.push_uci(played)

    @torch.inference_mode()
    def _assess(self, inputs: Iterable[Input]) -> list[MaiaFeature]:
        return [assessment for batch in batched(inputs, self.batch) for assessment in self._batch(batch)]

    def _batch(self, batch: tuple[Input, ...]) -> list[MaiaFeature]:
        tokens = torch.stack([item.tokens for item in batch]).to(self.config.device)
        mover, opponent = torch.tensor([item.elos for item in batch]).T.to(self.config.device)

        logits, values, ponders = self.model(tokens, mover, opponent)
        logits, values, ponders = logits.cpu(), values.softmax(-1).tolist(), ponders.tolist()

        features = []

        for item, row, (loss, draw, win), ponder in zip(batch, logits, values, ponders, strict=True):
            if not item.white:
                win, loss = loss, win

            indices = [self.indices[uci if item.white else mirror_move(uci)] for uci in item.legal]
            probabilities = row[indices].softmax(-1).tolist()
            policy = dict(zip(item.legal, probabilities))
            feature = MaiaFeature(
                probability=policy[item.played] if item.played else None,
                entropy=-sum(p * math.log(p) for p in probabilities if p),
                ponder=ponder if self.config.include_time_info else None,
                win=win,
                draw=draw,
                loss=loss,
            )
            features.append(feature)

        return features

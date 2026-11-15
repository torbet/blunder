import math
import random
from collections import deque
from collections.abc import AsyncGenerator
from dataclasses import dataclass, field
from datetime import UTC, datetime
from itertools import batched
from typing import NamedTuple

import chess
from rich import progress

from blunder.maia.core.maia import Maia
from blunder.shared.core.records import GameRecord, MoveRecord
from blunder.shared.models.analysis import LABELS, MaiaFeature
from blunder.shared.models.game import Elos, Players, Result
from blunder.stockfish.core.stockfish import Stockfish
from blunder.synthetic.core.config import Style, SyntheticConfig
from blunder.synthetic.core.openings import Openings

MAX_PLIES = 300
MIN_TIME = 0.1  # the shortest a move takes, and the least time a side can move with

WINNERS: dict[bool | None, Result] = {True: "white", False: "black", None: "draw"}

# Human move times, fitted on 88k moves of fair FICS games. Maia's ponder predicts them; entropy and clock add nothing.
INSTANT = (2.47, -3.29)  # logistic intercept and slope on log1p(ponder) for moves played instantly
SLOWNESS = (0.095, 0.80)  # intercept and slope of log1p(time) on log1p(ponder) for the rest
SPEED = 0.16  # standard deviation of a player's speed in log1p(time)
NOISE = 0.54  # standard deviation of the rest


@dataclass
class Match:
    """A game in progress. A side without a style plays fair."""

    game: GameRecord
    styles: tuple[Style | None, Style | None]
    speeds: tuple[float, float]
    book: deque[str]
    clocks: list[float]
    board: chess.Board = field(default_factory=chess.Board)

    @property
    def clock(self) -> float:
        return self.clocks[len(self.game.moves) % 2]

    @property
    def playing(self) -> bool:
        return len(self.game.moves) < MAX_PLIES and not (self.board.is_game_over() or self.clock < MIN_TIME)

    @property
    def result(self) -> Result:
        if outcome := self.board.outcome():
            return WINNERS[outcome.winner]

        return WINNERS[not self.board.turn] if self.clock < MIN_TIME else "draw"

    def push(self, move: MoveRecord) -> None:
        self.clocks[move.ply % 2] += self.game.control.increment - (move.time or 0)
        self.game.moves.append(move)
        self.board.push_uci(move.uci)


class Turn(NamedTuple):
    match: Match
    move: MoveRecord
    feature: MaiaFeature
    style: Style | None


class Generator:
    """Plays Maia against Maia. A cheating side swaps in Stockfish when its style calls for it."""

    def __init__(self, config: SyntheticConfig) -> None:
        self.config = config
        self.maia = Maia(config.model, config.batch)
        self.stockfish = Stockfish(config.depth)
        self.openings = Openings()

    async def generate(self, limit: int) -> AsyncGenerator[GameRecord]:
        random.seed(self.config.seed)

        with progress.Progress() as bars:
            task = bars.add_task("Generating", total=limit)

            async with self.stockfish.open():
                for wave in batched(range(limit), self.config.batch):
                    matches = [self.start(index) for index in wave]

                    while live := [match for match in matches if match.playing]:
                        await self.play(live)

                    for match in matches:
                        match.game.result = match.result
                        yield match.game

                    bars.advance(task, len(matches))

    def start(self, index: int) -> Match:
        """Games cycle through the outcomes, cheating sides draw a style, and play opens with part of a known line."""
        elo = random.gauss(self.config.elos.mean, self.config.elos.deviation)
        control = random.choice(self.config.controls)
        white, black = (
            random.choice(self.config.styles) if cheat else None for cheat in list(LABELS)[index % len(LABELS)]
        )
        game = GameRecord(
            source="synthetic",
            key=f"{self.config.seed}:{index}",
            players=Players(white=self.player(white), black=self.player(black)),
            result="draw",
            elos=Elos(white=self.rate(elo), black=self.rate(elo)),
            control=control,
            played=datetime.now(UTC),
            moves=[],
        )
        speeds = (random.gauss(0, SPEED), random.gauss(0, SPEED))
        return Match(
            game=game,
            styles=(white, black),
            speeds=speeds,
            book=deque(self.openings.sample()),
            clocks=[control.base] * 2,
        )

    def rate(self, elo: float) -> int:
        return round(random.gauss(elo, self.config.elos.gap))

    async def play(self, matches: list[Match]) -> None:
        moves = self.maia.play([match.game for match in matches])
        turns = [self.turn(match, move, feature) for match, (move, feature) in zip(matches, moves, strict=True)]
        await self.cheat(turns)

        for match, move, feature, _ in turns:
            move.time = self.humanise(feature.ponder, match.speeds[move.ply % 2], match.clock)
            match.push(move)

    async def cheat(self, turns: list[Turn]) -> None:
        """Swap in the engine's move wherever a cheater's style calls for it."""
        cheats = [turn for turn in turns if turn.style and (turn.feature.entropy or 0.0) >= turn.style.entropy]
        regrets = await self.stockfish.regret([t.match.board for t in cheats], [t.move for t in cheats])

        for turn, regret in zip(cheats, regrets, strict=True):
            if regret.best != turn.move.uci and turn.style and regret.loss >= turn.style.regret:
                turn.move.uci, turn.move.label = regret.best, True

    @staticmethod
    def turn(match: Match, move: MoveRecord, feature: MaiaFeature) -> Turn:
        """Opening moves are played from the book, and nobody consults an engine for them."""
        if match.book:
            move.uci = match.book.popleft()
            return Turn(match, move, feature, None)

        return Turn(match, move, feature, match.styles[move.ply % 2])

    @staticmethod
    def humanise(ponder: float | None, speed: float, clock: float) -> float:
        expected = math.log1p(ponder or 0.0)
        bias, slope = INSTANT

        if random.random() < 1 / (1 + math.exp(-(bias + slope * expected))):
            return 0.0

        bias, slope = SLOWNESS
        seconds = math.expm1(bias + slope * expected + speed + random.gauss(0, NOISE))
        return round(min(max(seconds, MIN_TIME), clock), 1)

    @staticmethod
    def player(style: Style | None) -> str:
        return f"maia+{style.name}" if style else "maia"

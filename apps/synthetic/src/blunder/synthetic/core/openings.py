import csv
import random
from pathlib import Path

import chess

PATH = Path("storage/openings.tsv")


class Openings:
    """The named opening lines, each as its uci moves."""

    def __init__(self) -> None:
        self.lines: list[list[str]] = []

        with PATH.open() as file:
            for row in csv.DictReader(file, delimiter="\t"):
                if row["eco"] != "eco":  # the file repeats its header row between sections
                    board = chess.Board()
                    sans = [word for word in row["pgn"].split() if not word.endswith(".")]
                    self.lines.append([board.push_san(san).uci() for san in sans])

    def sample(self) -> list[str]:
        """The first moves of a random line, from none of them to all."""
        line = random.choice(self.lines)
        return line[: random.randint(0, len(line))]

from collections.abc import AsyncGenerator
from itertools import chain, islice
from pathlib import Path

from rich import progress

from blunder.shared.core.records import Record, Records
from blunder.shared.models.game import Label

CLASSES: dict[Label, str] = {
    (False, False): "none",
    (True, False): "white",
    (False, True): "black",
    (True, True): "both",
}


class Sampler:
    def __init__(self, limit: int) -> None:
        self.limit = limit

    async def sample(self, path: Path) -> AsyncGenerator[Record]:
        selected = self._select(path)

        for index, record in enumerate(islice(Records.load(path), max(selected) + 1)):
            if record.type == "analysis" or index in selected:
                yield record

    def _select(self, path: Path) -> set[int]:
        groups: dict[Label, list[int]] = {label: [] for label in CLASSES}

        with progress.Progress() as bars:
            tasks = {label: bars.add_task(name.capitalize(), total=self.limit) for label, name in CLASSES.items()}

            for index, record in enumerate(Records.load(path)):
                if record.type == "game" and (label := record.label) in CLASSES and len(groups[label]) < self.limit:
                    groups[label].append(index)
                    bars.advance(tasks[label])

                    if bars.finished:
                        return set(chain.from_iterable(groups.values()))

        counts = {CLASSES[label]: len(group) for label, group in groups.items()}
        raise ValueError(f"Not enough games to sample {self.limit} per class: {counts}")

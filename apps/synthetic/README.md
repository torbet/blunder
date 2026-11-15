# Synthetic

Generates labelled games in which a human-like player sometimes consults an engine.

## Layout

```
apps/synthetic/
└── src/blunder/synthetic/
    ├── __init__.py        the generate command
    └── core/
        ├── config.py      settings and cheating styles
        ├── generator.py   plays the games
        └── openings.py    opening lines
```

## Usage

```sh
uv run generate CONFIG OUTPUT [--limit N]
```

- `--limit` is the number of games (default 10,000).
- Run it from the repository root.
- Pass the output through `analyse` to extract features.
- Cheaters are named `maia+<style>` in each game's players.

Start from [`storage/example/synthetic.yml`](../../storage/example/synthetic.yml).

## Configuration

| Key              | Meaning                                                                 |
| ---------------- | ----------------------------------------------------------------------- |
| `seed`           | seeds the moves                                                         |
| `model`, `batch` | Maia model, and games played per wave                                   |
| `depth`          | Stockfish depth for cheaters                                            |
| `elos`           | `mean`, `deviation` between games, `gap` between the two sides          |
| `controls`       | time controls to pick from, each with `base` and `increment` in seconds |
| `styles`         | cheating styles: a `name`, a `regret` floor and an `entropy` floor      |

A style consults the engine only in positions at least as complex as its `entropy`.
It plays the engine's move only if Maia's own gives up at least `regret` centipawns.

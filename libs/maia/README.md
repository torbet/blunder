# Maia

A wrapper around Maia3, a neural network that plays like a human of a given Elo and predicts how long a human takes.

## Layout

```
libs/maia/
└── src/blunder/maia/
    └── core/
        └── maia.py   the Maia class
```

## Usage

```python
maia = Maia("maia3-23m-ponder", batch=256)
features = maia.features(games)
moves = maia.play(games)
```

- **`batch`** is the number of positions per model call.
- **`features(games)`** returns a `MaiaFeature` per move: probability, entropy, win/draw/loss and expected time.
- **`play(games)`** returns each game's next move, sampled from the policy, with its position's features.

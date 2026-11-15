# Shared

The records, data models and configs used by every app.

## Layout

```
libs/shared/
└── src/blunder/shared/
    ├── core/
    │   ├── config.py      base class for settings
    │   └── records.py     game, move, analysis records; JSONL
    ├── analysis/
    │   ├── __init__.py    the pipeline config
    │   ├── maia.py        maia step config
    │   ├── predict.py     predict step config
    │   ├── stockfish.py   stockfish step config
    │   └── train.py       train step and model config
    └── models/
        ├── __init__.py    id and timestamp mixins
        ├── analysis.py    features, predictions, outcomes
        └── game.py        game and move models
```

## Usage

```python
for record in Records.load(path):
    ...
```

- `Records.load` streams a records file.
- `Records.save` writes one.
- `LABELS` in `models/analysis.py` lists the four outcomes in the detector's output order.

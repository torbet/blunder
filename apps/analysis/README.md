# Analysis

Extracts features from games, trains a detector on them and predicts with it.

## Layout

```
apps/analysis/
└── src/blunder/analysis/
    ├── __init__.py       the analyse and sample commands
    ├── core/
    │   ├── config.py     registry location
    │   ├── model.py      the Detector transformer
    │   ├── pipeline.py   the pipeline and its steps
    │   ├── registry.py   versioned model storage
    │   └── sampler.py    class-balanced sampling
    ├── maia/
    │   └── step.py       extracts Maia features
    ├── predict/
    │   └── step.py       adds predictions
    ├── stockfish/
    │   └── step.py       extracts engine features
    └── train/
        ├── step.py       the train step
        └── trainer.py    splits, training loop, metrics
```

## Usage

```sh
uv run analyse CONFIG INPUT OUTPUT
uv run sample INPUT OUTPUT [--limit N]
```

- **`analyse`** streams records through the steps in the config and writes them out.
- **`sample`** picks `--limit` games per outcome (default 10,000) to balance the four classes.

## Configuration

A pipeline config lists the steps to run, in order.
Records are processed `chunk` games at a time.

```yaml
chunk: 100

steps:
  - type: stockfish
    depth: 10

  - type: maia
    model: maia3-23m-ponder
    batch: 256
```

Examples are in `storage/example`:

- [`pipeline.yml`](../../storage/example/pipeline.yml) extracts features.
- [`train.yml`](../../storage/example/train.yml) extracts features and trains a detector.
- [`predict.yml`](../../storage/example/predict.yml) extracts features and predicts.

`train` and `predict` read the features already on the records.
List the feature steps before them, or run them on an analysed file.

Trained models are saved as numbered versions under `ANALYSIS__REGISTRY` in `.env`.

## Steps

### `stockfish`

Extracts the engine's evaluation and best move for every position.

| Setting | Meaning                   |
| ------- | ------------------------- |
| `depth` | search depth per position |

### `maia`

Extracts Maia's probability for the played move, its entropy, win/draw/loss and expected move time.

| Setting | Meaning                                     |
| ------- | ------------------------------------------- |
| `model` | Maia model name, such as `maia3-23m-ponder` |
| `batch` | positions per model call                    |

### `train`

Trains the detector on the labelled games and saves it as the next version.
Games without labels are skipped.
It prints validation metrics each epoch and test metrics at the end.

| Setting  | Meaning                                        |
| -------- | ---------------------------------------------- |
| `epochs` | passes over the training games                 |
| `batch`  | games per step                                 |
| `lr`     | peak learning rate                             |
| `seed`   | seeds initialisation and shuffling             |
| `model`  | `dim`, `layers` and `heads` of the transformer |

### `predict`

Adds a cheating probability to every move and four outcome probabilities to every game.

| Setting   | Meaning                           |
| --------- | --------------------------------- |
| `version` | the trained model version to load |

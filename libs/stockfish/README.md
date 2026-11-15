# Stockfish

An asynchronous pool of Stockfish engines.

## Layout

```
libs/stockfish/
└── src/blunder/stockfish/
    └── core/
        └── stockfish.py   the Stockfish class and Regret
```

## Usage

```python
stockfish = Stockfish(depth=10)

async with stockfish.open():
    features = await stockfish.features(games)
    regrets = await stockfish.regret(boards, moves)
```

- **`open()`** starts one engine per CPU core and stops them on exit.
- **`features(games)`** returns a `StockfishFeature` per move: the evaluation after it and the best move before it.
- **`regret(boards, moves)`** returns the engine's best move and the centipawns a candidate move gives up.

The `stockfish` binary must be on your `PATH`.

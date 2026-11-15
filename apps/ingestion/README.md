# Ingestion

Turns PGN games into records and loads records into the API.

## Layout

```
apps/ingestion/
└── src/blunder/ingestion/
    ├── __init__.py        the convert and ingest commands
    ├── core/
    │   ├── config.py      API address and batching
    │   └── ingestor.py    records to API requests
    └── pgn/
        └── converter.py   PGN games to records
```

## Usage

```sh
uv run convert INPUT OUTPUT [--limit N]
uv run ingest INPUT
```

- **`convert`** writes one record per game, up to `--limit` games.
- **`ingest`** posts a records file to the API in batches, so the API must be running.

## Configuration

`ingest` reads these from `.env`:

| Variable                 | Meaning             |
| ------------------------ | ------------------- |
| `API__HOST`, `API__PORT` | where the API is    |
| `INGESTION__BATCH_SIZE`  | records per request |
| `INGESTION__CONCURRENCY` | requests in flight  |

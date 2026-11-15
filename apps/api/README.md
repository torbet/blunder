# API

A FastAPI service that stores games, features and predictions in Postgres.

## Layout

```
apps/api/
├── migrations/               hand-written Alembic migrations
└── src/blunder/api/
    ├── __init__.py           the api command
    ├── core/
    │   ├── app.py            the FastAPI app
    │   ├── config.py         server and database settings
    │   ├── database.py       engine, session, table base
    │   └── dependencies.py   the session dependency
    ├── analysis/
    │   ├── models.py         analyses, features, predictions
    │   ├── router.py         the /analyses routes
    │   └── schemas.py        request and response schemas
    └── game/
        ├── models.py         games and moves
        ├── router.py         the /games routes
        └── schemas.py        request and response schemas
```

## Usage

```sh
docker compose up -d
(cd apps/api && uv run alembic upgrade head)
uv run api [--dev]
```

- `docker compose up -d` starts Postgres.
- `--dev` reloads the server when code changes.
- The interactive docs are at `/docs`.

## Configuration

Read from `.env`:

| Variable                                     | Meaning                       |
| -------------------------------------------- | ----------------------------- |
| `API__PORT`                                  | port to listen on             |
| `POSTGRES__HOST`, `__PORT`                   | where the database is         |
| `POSTGRES__USER`, `__PASSWORD`, `__DATABASE` | credentials and database name |

## Routes

| Route                                       | Does                                                |
| ------------------------------------------- | --------------------------------------------------- |
| `POST /games/`                              | Creates games with their moves.                     |
| `GET /games/{game_id}`                      | Returns a game with its moves.                      |
| `POST /analyses/`                           | Creates analyses, each recording a pipeline config. |
| `POST /analyses/{game_id}/features`         | Stores features for a game's moves.                 |
| `POST /analyses/{game_id}/move-predictions` | Stores move predictions.                            |
| `POST /analyses/{game_id}/game-predictions` | Stores game predictions.                            |

Every `POST` takes a list.

# alpacaQS

[![CI](https://github.com/rvgoing/alpacaqs/actions/workflows/ci.yml/badge.svg)](https://github.com/rvgoing/alpacaqs/actions/workflows/ci.yml)

A simple test website built with [FastAPI](https://fastapi.tiangolo.com/).

## Features

- HTML home page (Jinja2 template + static CSS) listing items, with a form to add new ones
- JSON API: `GET/POST /api/items`, `GET/PUT/DELETE /api/items/{id}`
- Items are stored in PostgreSQL when `DATABASE_URL` is set, otherwise in memory
- Health check at `/health`
- Auto-generated docs at `/docs` and `/redoc`

## Run locally

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Then open http://127.0.0.1:8000

## Tests

```bash
pytest
```

Tests never use `DATABASE_URL`, so they cannot touch the live database. By
default they use in-memory storage. To also run them against PostgreSQL, point
`TEST_DATABASE_URL` at a throwaway database (its `items` table is emptied):

```bash
TEST_DATABASE_URL=postgresql://postgres:postgres@localhost:5432/alpacaqs_test pytest
```

## Deploy to Render

This repo includes a `render.yaml` blueprint. In the Render dashboard choose
**New → Blueprint**, connect this GitHub repo, and click **Apply**.

## PostgreSQL

Set `DATABASE_URL` to a PostgreSQL connection string (never commit it):

```bash
export DATABASE_URL='postgresql://user:pass@host:5432/dbname'
```

On Render, add `DATABASE_URL` under the web service's **Environment** tab
(use the database's Internal URL). Visit `/db-check` to verify the connection.

On startup the app creates the `items` table if it does not exist and adds two
sample items when the table is empty. `/health` shows which storage is in use.

Database connections come from a pool (`psycopg_pool`) and are reused across
requests. `/db-check` reports `new_connection_ms` and `pooled_connection_ms` so
you can compare the cost of a fresh connection with a pooled one.

## Run with Docker (e.g. on TrueNAS)

```bash
cp .env.example .env   # then edit .env with your real DATABASE_URL
docker compose up -d --build
```

Open http://<host-ip>:8000. Files under `app/` are mounted into the container,
so edits reload automatically.

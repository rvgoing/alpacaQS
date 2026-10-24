# alpacaQS

A simple test website built with [FastAPI](https://fastapi.tiangolo.com/).

## Features

- HTML home page (Jinja2 template + static CSS) listing items, with a form to add new ones
- JSON API: `GET/POST /api/items`, `GET/DELETE /api/items/{id}` (in-memory store)
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

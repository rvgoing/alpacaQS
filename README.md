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

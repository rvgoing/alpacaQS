import os
from datetime import datetime, timezone
from pathlib import Path

import psycopg
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel

BASE_DIR = Path(__file__).resolve().parent

app = FastAPI(title="alpacaQS Test Site", version="0.1.0")
app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")
templates = Jinja2Templates(directory=BASE_DIR / "templates")


class Item(BaseModel):
    name: str
    description: str | None = None
    price: float


# In-memory store for demo purposes
items: dict[int, Item] = {
    1: Item(name="Alpaca", description="A fluffy test item", price=9.99),
    2: Item(name="Llama", description="Another test item", price=14.5),
}


@app.get("/", response_class=HTMLResponse)
def index(request: Request):
    return templates.TemplateResponse(
        request, "index.html", {"items": items, "year": datetime.now().year}
    )


@app.get("/health")
def health():
    return {"status": "ok", "time": datetime.now(timezone.utc).isoformat()}


@app.get("/db-check")
def db_check():
    url = os.environ.get("DATABASE_URL")
    if not url:
        raise HTTPException(status_code=503, detail="DATABASE_URL not set")
    try:
        with psycopg.connect(url, connect_timeout=5) as conn:
            version = conn.execute("select version()").fetchone()[0]
    except psycopg.Error as exc:
        raise HTTPException(status_code=503, detail=f"Database error: {exc}") from exc
    return {"status": "ok", "version": version}


@app.get("/api/items")
def list_items():
    return [{"id": item_id, **item.model_dump()} for item_id, item in items.items()]


@app.get("/api/items/{item_id}")
def get_item(item_id: int):
    if item_id not in items:
        raise HTTPException(status_code=404, detail="Item not found")
    return {"id": item_id, **items[item_id].model_dump()}


@app.post("/api/items", status_code=201)
def create_item(item: Item):
    item_id = max(items, default=0) + 1
    items[item_id] = item
    return {"id": item_id, **item.model_dump()}


@app.delete("/api/items/{item_id}", status_code=204)
def delete_item(item_id: int):
    if items.pop(item_id, None) is None:
        raise HTTPException(status_code=404, detail="Item not found")

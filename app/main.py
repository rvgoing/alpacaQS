import logging
import os
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from pathlib import Path

import psycopg
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from app.store import Item, create_store

BASE_DIR = Path(__file__).resolve().parent

# Load settings such as DATABASE_URL from .env for local development.
# Real environment variables (Render, CI) take precedence.
load_dotenv(BASE_DIR.parent / ".env")

logger = logging.getLogger("uvicorn.error")
store = create_store(os.environ.get("DATABASE_URL"))


@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        store.init()
        logger.info("Item storage: %s", store.name)
    except psycopg.Error as exc:
        # Keep the site up; item endpoints will report the database error
        logger.error("Could not initialise database: %s", exc)
    yield


app = FastAPI(title="alpacaQS Test Site", version="0.2.0", lifespan=lifespan)
app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")
templates = Jinja2Templates(directory=BASE_DIR / "templates")


@app.exception_handler(psycopg.Error)
async def database_error(request: Request, exc: psycopg.Error):
    return JSONResponse(status_code=503, content={"detail": f"Database error: {exc}"})


@app.get("/", response_class=HTMLResponse)
def index(request: Request):
    return templates.TemplateResponse(
        request,
        "index.html",
        {"items": store.list(), "storage": store.name, "year": datetime.now().year},
    )


@app.get("/health")
def health():
    return {
        "status": "ok",
        "storage": store.name,
        "time": datetime.now(timezone.utc).isoformat(),
    }


@app.get("/db-check")
def db_check():
    url = os.environ.get("DATABASE_URL")
    if not url:
        raise HTTPException(status_code=503, detail="DATABASE_URL not set")
    with psycopg.connect(url, connect_timeout=5) as conn:
        version = conn.execute("select version()").fetchone()[0]
    return {"status": "ok", "version": version}


@app.get("/api/items")
def list_items():
    return store.list()


@app.get("/api/items/{item_id}")
def get_item(item_id: int):
    item = store.get(item_id)
    if item is None:
        raise HTTPException(status_code=404, detail="Item not found")
    return item


@app.post("/api/items", status_code=201)
def create_item(item: Item):
    return store.create(item)


@app.put("/api/items/{item_id}")
def update_item(item_id: int, item: Item):
    updated = store.update(item_id, item)
    if updated is None:
        raise HTTPException(status_code=404, detail="Item not found")
    return updated


@app.delete("/api/items/{item_id}", status_code=204)
def delete_item(item_id: int):
    if not store.delete(item_id):
        raise HTTPException(status_code=404, detail="Item not found")

"""Item storage: PostgreSQL when DATABASE_URL is set, otherwise in memory."""

from psycopg.rows import dict_row
from psycopg_pool import ConnectionPool
from pydantic import BaseModel


class Item(BaseModel):
    name: str
    description: str | None = None
    price: float


SAMPLE_ITEMS = [
    Item(name="Alpaca", description="A fluffy test item", price=9.99),
    Item(name="Llama", description="Another test item", price=14.5),
]


class MemoryStore:
    name = "memory"

    def __init__(self):
        self.reset()

    def init(self):
        pass

    def close(self):
        pass

    def reset(self):
        self._items = {i: item for i, item in enumerate(SAMPLE_ITEMS, start=1)}

    def list(self) -> list[dict]:
        return [{"id": i, **item.model_dump()} for i, item in self._items.items()]

    def get(self, item_id: int) -> dict | None:
        item = self._items.get(item_id)
        return {"id": item_id, **item.model_dump()} if item else None

    def create(self, item: Item) -> dict:
        item_id = max(self._items, default=0) + 1
        self._items[item_id] = item
        return {"id": item_id, **item.model_dump()}

    def update(self, item_id: int, item: Item) -> dict | None:
        if item_id not in self._items:
            return None
        self._items[item_id] = item
        return {"id": item_id, **item.model_dump()}

    def delete(self, item_id: int) -> bool:
        return self._items.pop(item_id, None) is not None


SCHEMA = """
CREATE TABLE IF NOT EXISTS items (
    id SERIAL PRIMARY KEY,
    name TEXT NOT NULL,
    description TEXT,
    price NUMERIC(10, 2) NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
)
"""

# Cast price so the API returns a JSON number rather than a Decimal string
COLUMNS = "id, name, description, price::float8 AS price"


class PostgresStore:
    name = "postgresql"

    def __init__(self, url: str):
        # Reuse open connections instead of connecting (TCP + TLS + login)
        # on every request. Idle connections are recycled after 5 minutes.
        # Autocommit saves the BEGIN/COMMIT round trips around single statements.
        self.pool = ConnectionPool(
            url,
            min_size=1,
            max_size=5,
            max_idle=300,
            timeout=10,
            open=False,
            kwargs={"connect_timeout": 5, "row_factory": dict_row, "autocommit": True},
        )

    def _connect(self):
        return self.pool.connection()

    def init(self):
        """Open the pool, create the table, and add sample items if it is empty."""
        self.pool.open()
        with self._connect() as conn, conn.transaction():
            conn.execute(SCHEMA)
            if conn.execute("SELECT count(*) AS n FROM items").fetchone()["n"] == 0:
                self._seed(conn)

    def close(self):
        self.pool.close()

    def reset(self):
        """Empty the table and re-add sample items. Used by tests only."""
        with self._connect() as conn, conn.transaction():
            conn.execute(SCHEMA)
            conn.execute("TRUNCATE items RESTART IDENTITY")
            self._seed(conn)

    def _seed(self, conn):
        for item in SAMPLE_ITEMS:
            conn.execute(
                "INSERT INTO items (name, description, price) VALUES (%s, %s, %s)",
                (item.name, item.description, item.price),
            )

    def list(self) -> list[dict]:
        with self._connect() as conn:
            return conn.execute(f"SELECT {COLUMNS} FROM items ORDER BY id").fetchall()

    def get(self, item_id: int) -> dict | None:
        with self._connect() as conn:
            return conn.execute(
                f"SELECT {COLUMNS} FROM items WHERE id = %s", (item_id,)
            ).fetchone()

    def create(self, item: Item) -> dict:
        with self._connect() as conn:
            return conn.execute(
                "INSERT INTO items (name, description, price) VALUES (%s, %s, %s)"
                f" RETURNING {COLUMNS}",
                (item.name, item.description, item.price),
            ).fetchone()

    def update(self, item_id: int, item: Item) -> dict | None:
        with self._connect() as conn:
            return conn.execute(
                "UPDATE items SET name = %s, description = %s, price = %s"
                f" WHERE id = %s RETURNING {COLUMNS}",
                (item.name, item.description, item.price, item_id),
            ).fetchone()

    def delete(self, item_id: int) -> bool:
        with self._connect() as conn:
            return conn.execute("DELETE FROM items WHERE id = %s", (item_id,)).rowcount > 0


def create_store(database_url: str | None):
    return PostgresStore(database_url) if database_url else MemoryStore()

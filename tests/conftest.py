import os

# Tests must never touch the live database in .env. They use TEST_DATABASE_URL
# (a throwaway database whose items table is emptied) or in-memory storage.
os.environ["DATABASE_URL"] = os.environ.get("TEST_DATABASE_URL", "")

import pytest  # noqa: E402

from app.main import store  # noqa: E402


@pytest.fixture(autouse=True)
def reset_store():
    store.reset()

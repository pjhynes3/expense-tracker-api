import os

import pytest
from dotenv import load_dotenv
from fastapi.testclient import TestClient
from sqlalchemy.engine import make_url

# Load TEST_DATABASE_URL from local .env file
load_dotenv()

TEST_DATABASE_URL = os.environ["TEST_DATABASE_URL"]

# Critical safety check: test are allowed to delete data
database_name = make_url(TEST_DATABASE_URL).database

if database_name is None or not database_name.endswith("_test"):
    raise RuntimeError(
        "TEST_DATABASE_URL must point to a database ending in '_test'"
    )


# The application reads DATABASE_URL when its modules are imported.
# Override it before importing anything from app.
os.environ["DATABASE_URL"] = TEST_DATABASE_URL

from app.cache import cache_clear
from app.database import SessionLocal
from app.db_models import ExpenseRow, UserRow
from app.solution import app


def clear_test_data() -> None:
    """
    Remove all application data from the dedicated test database.
    Expenses must be deleted before users because expenses reference users.
    """

    db = SessionLocal()

    try:
        db.query(ExpenseRow).delete()
        db.query(UserRow).delete()
        db.commit()
    finally:
        db.close()

    cache_clear()

@pytest.fixture
def client():
    """
    Give each test a clean FastAPI TestClient and clean database.
    """
    clear_test_data()

    with TestClient(app) as test_client:
        yield test_client

    clear_test_data()
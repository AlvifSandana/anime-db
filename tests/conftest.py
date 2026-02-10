import asyncio
import os
import sys
import tempfile
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.db.session import SessionLocal, Base, engine
from app.main import create_app


@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture()
def db_session():
    db_fd, db_path = tempfile.mkstemp()
    os.close(db_fd)
    os.environ["DB_URL"] = f"sqlite:///{db_path}"

    # Recreate engine/session bound to temp DB
    from app.db.session import SessionLocal as TestSessionLocal, Base as TestBase, engine as test_engine

    TestBase.metadata.create_all(bind=test_engine)
    session = TestSessionLocal()
    try:
        yield session
    finally:
        session.close()
        os.remove(db_path)


@pytest.fixture()
def client():
    app = create_app()
    with TestClient(app) as c:
        yield c

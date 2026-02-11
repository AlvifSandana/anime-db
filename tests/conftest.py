import asyncio
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.db import session as db_session_module
from app.api.routes import anime as anime_routes
from app.main import create_app


@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture()
def test_db(tmp_path):
    db_path = tmp_path / "test.db"
    engine = create_engine(f"sqlite:///{db_path}", connect_args={"check_same_thread": False})
    session_local = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    old_engine = db_session_module.engine
    old_session_local = db_session_module.SessionLocal

    db_session_module.engine = engine
    db_session_module.SessionLocal = session_local
    db_session_module.Base.metadata.create_all(bind=engine)
    try:
        yield session_local
    finally:
        db_session_module.Base.metadata.drop_all(bind=engine)
        engine.dispose()
        db_session_module.engine = old_engine
        db_session_module.SessionLocal = old_session_local


@pytest.fixture()
def db_session(test_db):
    session = test_db()
    try:
        yield session
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


@pytest.fixture()
def client(test_db):
    app = create_app()

    def override_get_db():
        db = test_db()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[anime_routes.get_db] = override_get_db
    with TestClient(app) as c:
        yield c

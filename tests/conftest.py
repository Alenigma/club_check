import os
import tempfile
import importlib
import pytest
from fastapi.testclient import TestClient


@pytest.fixture(scope="session")
def temp_db_url():
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    yield f"sqlite:///{path}"
    try:
        os.remove(path)
    except OSError:
        pass


@pytest.fixture()
def client(temp_db_url, monkeypatch):
    # Configure environment for this test run
    monkeypatch.setenv("CLUB_CHECK_DATABASE_URL", temp_db_url)
    monkeypatch.setenv("CLUB_CHECK_CREATE_TABLES_ON_STARTUP", "false")
    monkeypatch.setenv("CLUB_CHECK_SEED_ON_STARTUP", "false")
    monkeypatch.setenv("CLUB_CHECK_SECRET_KEY", "test-secret-key")

    # Reload config and database to pick up env
    import app.config as cfg
    importlib.reload(cfg)
    import app.database as db
    importlib.reload(db)
    import app.models as models
    import app.main as main
    importlib.reload(main)

    # Create tables
    models.Base.metadata.create_all(bind=db.engine)

    test_client = TestClient(main.app)
    try:
        yield test_client
    finally:
        models.Base.metadata.drop_all(bind=db.engine)



import os
import tempfile
import shutil
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from alembic.config import Config
from alembic import command

from app.main import app
from app.config import settings

@pytest.fixture(scope="session")
def temp_db_dir():
    d = tempfile.mkdtemp(prefix="legacyshop-test-")
    yield d
    shutil.rmtree(d, ignore_errors=True)

@pytest.fixture(scope="session", autouse=True)
def configure_env(temp_db_dir):
    os.environ["APP_ENV"] = "test"
    db_path = str(Path(temp_db_dir) / "test.db")
    os.environ["DATABASE_URL"] = f"sqlite:///{db_path}"
    os.environ["PAYMENT_RANDOM_ENABLED"] = "false"
    os.environ["SCHEDULER_ENABLED"] = "false"
    yield

@pytest.fixture(scope="session")
def migrated_db(configure_env):
    alembic_cfg = Config("alembic.ini")
    command.upgrade(alembic_cfg, "head")
    return True

@pytest.fixture(scope="session")
def client(migrated_db):
    return TestClient(app)

import os
import sys
import tempfile
import shutil
from pathlib import Path

TMP_BASE = tempfile.mkdtemp(prefix="legacyshop-test-")
os.environ["APP_ENV"] = "test"
os.environ["DATABASE_URL"] = f"sqlite:///{Path(TMP_BASE) / 'test.db'}"
os.environ["PAYMENT_RANDOM_ENABLED"] = "false"
os.environ["SCHEDULER_ENABLED"] = "false"

import pytest
from fastapi.testclient import TestClient
from alembic.config import Config
from alembic import command

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.main import app

@pytest.fixture(scope="session", autouse=True)
def migrated_db():
    alembic_cfg = Config("alembic.ini")
    command.upgrade(alembic_cfg, "head")
    from app.db import seed as seed_mod
    seed_mod.main()
    yield
    shutil.rmtree(TMP_BASE, ignore_errors=True)

@pytest.fixture(scope="session")
def client(migrated_db):
    return TestClient(app)

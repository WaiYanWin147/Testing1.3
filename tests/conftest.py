# tests/conftest.py
import os
import sys
import types
import pytest

# --- Dynamic stub importer for any missing app.entity/* or app.control/* ---
class _StubLoader:
    def find_spec(self, fullname, path, target=None):
        if fullname.startswith("app.entity.") or fullname.startswith("app.control."):
            return types.SimpleNamespace(loader=self, origin="stub")
        if fullname == "app.config":
            return types.SimpleNamespace(loader=self, origin="stub")
        return None

    def create_module(self, spec):
        return None  # use exec_module

    def exec_module(self, module):
        name = module.__name__
        if name == "app.config":
            # Provide a minimal Config so your factory can import it
            class Config:
                SECRET_KEY = "test"
                SQLALCHEMY_DATABASE_URI = os.environ.get("DATABASE_URL", "sqlite://")
                SQLALCHEMY_TRACK_MODIFICATIONS = False
                TESTING = True
            module.Config = Config
            return

        # For app.entity.* or app.control.* just provide an empty module
        # (you can add attributes here later if a route actually uses them)
        pass

# Install the stub loader
sys.meta_path.insert(0, _StubLoader())

# Now it's safe to import your app factory
from app import create_app  # noqa: E402


@pytest.fixture
def client(tmp_path, monkeypatch):
    # Temporary SQLite DB file for the test run
    db_file = tmp_path / "test.db"
    os.environ["DATABASE_URL"] = f"sqlite:///{db_file}"

    app = create_app()

    # Minimal in-memory templates so render_template works in smoke tests
    from jinja2 import DictLoader
    app.jinja_loader = DictLoader({
        "index.html": "<h1>Home</h1>",
        "auth/login.html": "<form method='post'></form>",
    })

    with app.test_client() as c:
        yield c

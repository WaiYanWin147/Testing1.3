import os, sys, types, pytest

# --- Dynamically stub any missing imports your app does at import time ---
class _StubLoader:
    def find_spec(self, fullname, path, target=None):
        if fullname.startswith("app.entity.") or fullname.startswith("app.control."):
            return types.SimpleNamespace(loader=self, origin="stub")
        if fullname == "app.config":
            return types.SimpleNamespace(loader=self, origin="stub")
        return None
    def create_module(self, spec): return None
    def exec_module(self, module):
        if module.__name__ == "app.config":
            class Config:
                SECRET_KEY = "test"
                SQLALCHEMY_DATABASE_URI = os.environ.get("DATABASE_URL", "sqlite://")
                SQLALCHEMY_TRACK_MODIFICATIONS = False
                TESTING = True
            module.Config = Config  # provide Config for app factory
            return
        # otherwise leave stub module empty

sys.meta_path.insert(0, _StubLoader())

from app import create_app  # safe after stubs are in place

@pytest.fixture
def client(tmp_path):
    db_file = tmp_path / "test.db"
    os.environ["DATABASE_URL"] = f"sqlite:///{db_file}"
    app = create_app()

    # Minimal in-memory templates so render_template() works
    from jinja2 import DictLoader
    app.jinja_loader = DictLoader({
        "index.html": "<h1>Home</h1>",
        "auth/login.html": "<form method='post'></form>",
    })

    with app.test_client() as c:
        yield c

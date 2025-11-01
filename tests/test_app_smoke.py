import os

# Use an in-memory SQLite DB for tests to avoid file writes
os.environ["DATABASE_URL"] = "sqlite:///:memory:"

from app import create_app  # import after setting env var

def test_create_app():
    app = create_app()
    assert app is not None

def test_root_route():
    app = create_app()
    app.testing = True
    client = app.test_client()
    resp = client.get("/")
    assert resp.status_code == 200  # your "/" is public

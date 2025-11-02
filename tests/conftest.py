import os, tempfile, pytest
from app import create_app  # or from main import app if you don’t use a factory

@pytest.fixture
def client():
    db_fd, db_path = tempfile.mkstemp()
    os.environ["DATABASE_URL"] = f"sqlite:///{db_path}"
    app = create_app({"TESTING": True})
    with app.test_client() as client:
        yield client
    os.close(db_fd)
    os.remove(db_path)

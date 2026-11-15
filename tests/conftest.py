import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.database import db

@pytest.fixture
def client():
    return TestClient(app)

@pytest.fixture
def test_db():
    return db

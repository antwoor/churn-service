import pytest
from fastapi.testclient import TestClient

from dino.service.app import app


@pytest.fixture(scope="session")
def client():
    with TestClient(app) as c:
        yield c


@pytest.fixture()
def good_row():
    return {
        "dino_type": "large theropod",
        "length_m": 12.0,
        "period": "Late Jurassic",
        "lived_in": "USA",
    }

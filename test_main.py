import os

os.environ["API_TOKEN"] = "test-only-token"
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)


def test_create_book_without_token():
    response = client.post(
        "/books",
        json={"title": "Test Book", "author": "Test Author"}
    )

    assert response.status_code == 401

def test_create_book_with_invalid_token():
    response = client.post(
        "/books",
        headers={"Authorization": "Bearer wrong-token"},
        json={"title": "Test Book", "author": "Test Author"}
    )

    assert response.status_code == 401
import os
import pytest 
import database

os.environ["API_TOKEN"] = "test-only-token"
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

@pytest.fixture(autouse=True)
def isolated_database(tmp_path, monkeypatch):
    test_db = tmp_path / "test_books.db"
    monkeypatch.setattr(database, "DB_PATH", test_db)
    database.init_db()

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

def test_create_book_with_valid_token():
    response = client.post(
        "/books",
        headers={"Authorization": "Bearer test-only-token"},
        json={"title": "Test Book", "author": "Test Author"}
    )

    assert response.status_code == 201

    data = response.json()
    assert isinstance(data["id"], int)
    assert data["title"] == "Test Book"
    assert data["author"] == "Test Author"

    saved = client.get(f"/books/{data['id']}")

    assert saved.status_code == 200
    assert saved.json() == data

def test_create_book_with_blank_title():
    response = client.post(
        "/books",
        headers={"Authorization": "Bearer test-only-token"},
        json={"title": "   ", "author": "Test Author"}
    )

    assert response.status_code == 422

    count_response = client.get("/books/count")
    assert count_response.status_code == 200
    assert count_response.json() == {"count": 0}

def test_get_missing_book():
    response = client.get("/books/999")

    assert response.status_code == 404
    assert response.json() == {"detail": "Book not found"}

def test_update_book_title():
    headers = {"Authorization": "Bearer test-only-token"}

    created = client.post(
        "/books",
        headers=headers,
        json={"title": "Original Title", "author": "Original Author"}
    )
    assert created.status_code == 201
    book_id = created.json()["id"]

    updated = client.patch(
        f"/books/{book_id}",
        headers=headers,
        json={"title": "Updated Title"}
    )

    assert updated.status_code == 200
    assert updated.json() == {
        "id": book_id,
        "title": "Updated Title",
        "author": "Original Author"
    }

    saved = client.get(f"/books/{book_id}")
    assert saved.status_code == 200
    assert saved.json() == updated.json()

def test_delete_book():
    headers = {"Authorization": "Bearer test-only-token"}

    created = client.post(
        "/books",
        headers=headers,
        json={"title": "Book to Delete", "author": "Test Author"}
    )
    assert created.status_code == 201
    book_id = created.json()["id"]

    deleted = client.delete(
        f"/books/{book_id}",
        headers=headers
    )

    assert deleted.status_code == 200
    assert deleted.json() == {"message": "Book deleted"}

    retrieved = client.get(f"/books/{book_id}")
    assert retrieved.status_code == 404

def test_filter_books_by_author():
    headers = {"Authorization": "Bearer test-only-token"}

    first = client.post(
        "/books",
        headers=headers,
        json={"title": "Atomic Habits", "author": "James Clear"}
    )
    second = client.post(
        "/books",
        headers=headers,
        json={"title": "Deep Work", "author": "Cal Newport"}
    )

    assert first.status_code == 201
    assert second.status_code == 201

    response = client.get(
        "/books",
        params={"author": "James Clear"}
    )

    assert response.status_code == 200
    assert response.json() == [first.json()]

def test_paginate_books():
    headers = {"Authorization": "Bearer test-only-token"}
    created_books = []

    for title in ["First Book", "Second Book", "Third Book"]:
        created = client.post(
            "/books",
            headers=headers,
            json={"title": title, "author": "Test Author"}
        )
        assert created.status_code == 201
        created_books.append(created.json())

    response = client.get(
        "/books",
        params={"limit": 1, "offset": 1}
    )

    assert response.status_code == 200
    assert response.json() == [created_books[1]]

def test_sort_books_by_title():
    headers = {"Authorization": "Bearer test-only-token"}
    created_books = {}

    for title in ["Zebra", "Apple", "Mango"]:
        created = client.post(
            "/books",
            headers=headers,
            json={"title": title, "author": "Test Author"}
        )
        assert created.status_code == 201
        created_books[title] = created.json()

    response = client.get(
        "/books",
        params={"sort_by": "title"}
    )

    assert response.status_code == 200
    assert response.json() == [
        created_books["Apple"],
        created_books["Mango"],
        created_books["Zebra"]
    ]
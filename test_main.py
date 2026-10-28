import os
import pytest 
import database
import jwt
from datetime import datetime, timedelta, timezone
from fastapi.testclient import TestClient
from main import app

TEST_SECRET = "test-only-signing-secret-not-for-real-use"

client = TestClient(app)

@pytest.fixture(autouse=True)
def isolated_database(tmp_path, monkeypatch):
    monkeypatch.setenv("JWT_SECRET_KEY", TEST_SECRET)
    monkeypatch.setattr(database, "DB_PATH", tmp_path / "test_books.db")
    database.init_db()

@pytest.fixture
def auth_headers():
    credentials = {
        "username": "api_test_user",
        "password": "example-test-password"
    }

    registered = client.post("/register", json=credentials)
    assert registered.status_code == 201

    logged_in = client.post("/login", json=credentials)
    assert logged_in.status_code == 200

    token = logged_in.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}

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


def test_create_book_with_valid_token(auth_headers):
    response = client.post(
        "/books",
        headers=auth_headers,
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


def test_create_book_with_blank_title(auth_headers):
    response = client.post(
        "/books",
        headers=auth_headers,
        json={"title": "   ", "author": "Test Author"}
    )

    assert response.status_code == 422

    count_response = client.get("/books/count")
    assert count_response.status_code == 200
    assert count_response.json() == {"count": 0}


def test_get_missing_book(auth_headers):
    response = client.get("/books/999")

    assert response.status_code == 404
    assert response.json() == {"detail": "Book not found"}

def test_update_book_title(auth_headers):
    headers = auth_headers

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

def test_delete_book(auth_headers):
    headers = auth_headers

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

def test_filter_books_by_author(auth_headers):
    headers = auth_headers

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

def test_paginate_books(auth_headers):
    headers = auth_headers
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

def test_sort_books_by_title(auth_headers):
    headers = auth_headers
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

def test_register_user():
    response = client.post(
        "/register",
        json={
            "username": "testuser",
            "password": "example-test-password"
        }
    )

    assert response.status_code == 201

    data = response.json()
    assert isinstance(data["id"], int)
    assert data["username"] == "testuser"
    assert set(data) == {"id", "username"}

def test_register_duplicate_username():
    user = {
        "username": "testuser",
        "password": "example-test-password"
    }

    first = client.post("/register", json=user)
    assert first.status_code == 201

    second = client.post("/register", json=user)

    assert second.status_code == 409
    assert second.json() == {
        "detail": "Username already exists"
    }

def test_login_with_correct_password(monkeypatch):
    monkeypatch.setenv(
        "JWT_SECRET_KEY",
        "test-only-signing-secret-not-for-real-use"
    )

    registered = client.post(
        "/register",
        json={
            "username": "testuser",
            "password": "example-test-password"
        }
    )
    assert registered.status_code == 201

    response = client.post(
        "/login",
        json={
            "username": "testuser",
            "password": "example-test-password"
        }
    )

    assert response.status_code == 200

    data = response.json()
    assert data["token_type"] == "bearer"
    assert isinstance(data["access_token"], str)
    assert data["access_token"]

def test_login_with_wrong_password():
    registered = client.post(
        "/register",
        json={
            "username": "testuser",
            "password": "example-test-password"
        }
    )
    assert registered.status_code == 201

    response = client.post(
        "/login",
        json={
            "username": "testuser",
            "password": "wrong-password"
        }
    )

    assert response.status_code == 401
    assert response.json() == {
        "detail": "Invalid username or password"
    }

def test_login_with_unknown_username():
    response = client.post(
        "/login",
        json={
            "username": "unknownuser",
            "password": "example-test-password"
        }
    )

    assert response.status_code == 401
    assert response.json() == {
        "detail": "Invalid username or password"
    }

def test_expired_token_is_rejected(auth_headers):
    user = database.get_user_by_username("api_test_user")

    token = jwt.encode(
        {
            "sub": str(user["id"]),
            "exp": datetime.now(timezone.utc) - timedelta(minutes=1)
        },
        TEST_SECRET,
        algorithm="HS256"
    )

    response = client.post(
        "/books",
        headers={"Authorization": f"Bearer {token}"},
        json={"title": "Test Book", "author": "Test Author"}
    )

    assert response.status_code == 401
    assert database.count_books() == 0


def test_tampered_token_is_rejected(auth_headers):
    token = auth_headers["Authorization"].split(" ", 1)[1]
    header, payload, signature = token.split(".")

    # Change the signature so it no longer matches the token.
    replacement = "A" if signature[0] != "A" else "B"
    signature = replacement + signature[1:]
    tampered_token = f"{header}.{payload}.{signature}"

    response = client.post(
        "/books",
        headers={"Authorization": f"Bearer {tampered_token}"},
        json={"title": "Test Book", "author": "Test Author"}
    )

    assert response.status_code == 401
    assert database.count_books() == 0


def test_deleted_user_token_is_rejected(auth_headers):
    with database.sqlite3.connect(database.DB_PATH) as connection:
        connection.execute(
            "DELETE FROM users WHERE username = ?",
            ("api_test_user",)
        )

    response = client.post(
        "/books",
        headers=auth_headers,
        json={"title": "Test Book", "author": "Test Author"}
    )

    assert response.status_code == 401
    assert database.count_books() == 0
import sqlite3
from auth import hash_password, verify_password, create_access_token
from database import get_user_by_username
from database import create_user
import os
import secrets
from database import get_all_books
from database import get_book as get_book_from_db
from database import add_book
from database import update_book as update_book_in_db
from database import delete_book as delete_book_from_db
from database import count_books as count_books_in_db
from fastapi import FastAPI, HTTPException, Query, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, Field, ConfigDict, field_validator
from typing import Literal
from jwt.exceptions import InvalidTokenError
from auth import decode_access_token
from database import get_user_by_id

app = FastAPI()

bearer_scheme = HTTPBearer(auto_error=False)

def require_token(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme)
):
    unauthorized = HTTPException(
        status_code=401,
        detail="Missing or invalid token",
        headers={"WWW-Authenticate": "Bearer"}
    )

    if credentials is None:
        raise unauthorized

    if not os.getenv("JWT_SECRET_KEY"):
        raise HTTPException(
            status_code=503,
            detail="Authentication is not configured"
        )

    try:
        payload = decode_access_token(credentials.credentials)
        user_id = int(payload["sub"])
    except (InvalidTokenError, ValueError, TypeError, KeyError):
        raise unauthorized

    user = get_user_by_id(user_id)

    if user is None:
        raise unauthorized

    return user

class BookCreate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    title: str = Field(min_length=1)
    author: str = Field(min_length=1)

class BookUpdate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    title: str | None = Field(default=None, min_length=1)
    author: str | None = Field(default=None, min_length=1)

    @field_validator("title", "author")
    @classmethod
    def reject_null(cls, value):
        if value is None:
            raise ValueError("Field cannot be null")
        return value

class UserCreate(BaseModel):
    username: str = Field(
        min_length=3,
        max_length=30,
        pattern=r"^[A-Za-z0-9_]+$"
    )
    password: str = Field(min_length=15, max_length=128)

class UserLogin(BaseModel):
    username: str
    password: str

@app.get("/books/count")
def count_books():
    return {"count": count_books_in_db()}


@app.get("/books/{book_id}")
def get_book(book_id: int):
    book = get_book_from_db(book_id)

    if book is None:
        raise HTTPException(status_code=404, detail="Book not found")

    return book


@app.get("/books")
def get_books(
    author: str | None = None,
    limit: int = Query(default=10, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    sort_by: Literal["id", "title"] = "id"
):
    return get_all_books(
        author=author,
        limit=limit,
        offset=offset,
        sort_by=sort_by
    )

@app.get("/hello/{name}")
def greet_user(name: str):
    return {"message": f"Hello{name}"}

@app.post("/books", status_code=201)
def create_book(
    book: BookCreate,
    current_user: dict = Depends(require_token)
):
    new_id = add_book(
        book.title,
        book.author,
        current_user["id"]
    )
    return get_book_from_db(new_id)


@app.patch("/books/{book_id}")
def update_book(
    book_id: int,
    book: BookUpdate,
    current_user: dict = Depends(require_token)
):
    existing_book = get_book_from_db(book_id)

    if existing_book is None:
        raise HTTPException(status_code=404, detail="Book not found")

    if existing_book["owner_id"] != current_user["id"]:
        raise HTTPException(
            status_code=403,
            detail="Only the owner can modify this book"
        )

    changes = book.model_dump(exclude_unset=True)
    update_book_in_db(book_id, changes, current_user["id"])

    return get_book_from_db(book_id)


@app.delete("/books/{book_id}")
def delete_book(
    book_id: int,
    current_user: dict = Depends(require_token)
):
    existing_book = get_book_from_db(book_id)

    if existing_book is None:
        raise HTTPException(status_code=404, detail="Book not found")

    if existing_book["owner_id"] != current_user["id"]:
        raise HTTPException(
            status_code=403,
            detail="Only the owner can delete this book"
        )

    delete_book_from_db(book_id, current_user["id"])

    return {"message": "Book deleted"}

@app.get("/health")
def get_health():
    return {"status": "ok"}

@app.post("/register", status_code=201)
def register(user: UserCreate):
    password_hash = hash_password(user.password)

    try:
        user_id = create_user(user.username, password_hash)
    except sqlite3.IntegrityError:
        raise HTTPException(
            status_code=409,
            detail="Username already exists"
        )

    return {"id": user_id, "username": user.username}

@app.post("/login")
def login(credentials: UserLogin):
    user = get_user_by_username(credentials.username)

    if user is None or not verify_password(
        credentials.password, user["password_hash"]
    ):
        raise HTTPException(
            status_code=401,
            detail="Invalid username or password",
            headers={"WWW-Authenticate": "Bearer"}
        )

    token = create_access_token(user["id"])

    return {
        "access_token": token,
        "token_type": "bearer"
    }
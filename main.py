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

app = FastAPI()

bearer_scheme = HTTPBearer(auto_error=False)

def require_token(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme)
):
    expected_token = os.getenv("API_TOKEN")

    if not expected_token:
        raise HTTPException(
            status_code=503,
            detail="Authentication is not configured"
        )

    if credentials is None or not secrets.compare_digest(
        credentials.credentials, expected_token
    ):
        raise HTTPException(
            status_code=401,
            detail="Missing or invalid token",
            headers={"WWW-Authenticate": "Bearer"}
        )

class BookCreate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    title: str = Field(min_length=1)
    author: str = Field(min_length=1)

class BookUpdate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    title: str | None = None
    author: str | None = None

    @field_validator("title", "author")
    @classmethod
    def reject_null(cls, value):
        if value is None:
            raise ValueError("Field cannot be null")
        return value

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

@app.post(
    "/books",
    status_code=201,
    dependencies=[Depends(require_token)]
)
def create_book(book: BookCreate):
    new_id = add_book(book.title, book.author)
    return get_book_from_db(new_id)

@app.delete(
    "/books/{book_id}",
    dependencies=[Depends(require_token)]
)
def delete_book(book_id: int):
    deleted_count = delete_book_from_db(book_id)

    if deleted_count == 0:
        raise HTTPException(status_code=404, detail="Book not found")

    return {"message": "Book deleted"}

@app.patch(
    "/books/{book_id}",
    dependencies=[Depends(require_token)]
)
def update_book(book_id: int, book: BookUpdate):
    if get_book_from_db(book_id) is None:
        raise HTTPException(status_code=404, detail="Book not found")

    changes = book.model_dump(exclude_unset=True)
    update_book_in_db(book_id, changes)

    return get_book_from_db(book_id)

@app.get("/health")
def get_health():
    return {"status": "ok"}


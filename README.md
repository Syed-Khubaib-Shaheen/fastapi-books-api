# FastAPI Books API

A REST API built while learning backend development with Python,
FastAPI, and SQLite.

## Features

- Create, retrieve, update, and delete books
- Persistent SQLite storage
- Input validation and error handling
- Author filtering, pagination, and sorting
- Bearer token protection for POST, PATCH, and DELETE
- Automated tests for missing and invalid tokens

## Setup

Requires Python 3.13.

```bash
git clone https://github.com/Syed-Khubaib-Shaheen/fastapi-books-api.git
cd fastapi-books-api
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

## Run locally

Generate a local token:

```bash
export API_TOKEN="$(python -c 'import secrets; print(secrets.token_urlsafe(32))')"
```

To view and copy it locally:

```bash
printenv API_TOKEN
```

Start the server from the same terminal:

```bash
fastapi dev main.py
```

Interactive documentation: http://127.0.0.1:8000/docs

Click **Authorize** and enter the token value without the `Bearer` prefix.

The SQLite database and books table are created automatically when
the application is imported. The local database is excluded from Git.

## Endpoints

| Method | Path | Purpose | Token required |
|---|---|---|---|
| GET | `/health` | Basic health response | No |
| GET | `/books` | List books | No |
| GET | `/books/count` | Count all books | No |
| GET | `/books/{book_id}` | Retrieve one book | No |
| POST | `/books` | Create a book | Yes |
| PATCH | `/books/{book_id}` | Update selected fields | Yes |
| DELETE | `/books/{book_id}` | Delete a book | Yes |

List query parameters:

- `author`: exact author match
- `limit`: 1–100, default 10
- `offset`: zero or greater, default 0
- `sort_by`: `id` or `title`, default `id`

Example:

```text
/books?sort_by=title&limit=5&offset=0
```

## Run tests

```bash
python -m pytest -v
```

The development server does not need to be running.
Each test uses a fresh temporary SQLite database, keeping local book data untouched.

Seven tests cover:
- Missing and invalid authentication tokens
- Successful book creation and retrieval
- Rejection of a blank title without saving data
- Retrieval of a missing book
- Partial updates that preserve omitted fields
- Deletion followed by a lookup confirming removal
- Author filtering
- Pagination using limit and offset
- Sorting books by title

## Learning scope

Authentication currently uses one shared environment token.
User registration, login, individual user permissions, and expiring
tokens are not implemented yet.
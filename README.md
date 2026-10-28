# FastAPI Books API

A REST API built while learning backend development with Python,
FastAPI, and SQLite.

## Features

- Create, retrieve, update, and delete books
- Persistent SQLite storage
- Input validation and error handling
- Author filtering, pagination, and sorting
- User registration with unique usernames
- Argon2 password hashing
- Login with JWT access tokens that expire after 30 minutes
- Token protection for POST, PATCH, and DELETE book endpoints
- 21 automated tests

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

Generate a private signing secret and start the server
from the same terminal:

```bash
export JWT_SECRET_KEY="$(python -c 'import secrets; print(secrets.token_urlsafe(32))')"
fastapi dev main.py
```

Keep the signing secret private. Do not commit it or enter it
in the API documentation's Authorize box.

Generating a new signing secret invalidates tokens signed
with the previous secret.

Interactive documentation: http://127.0.0.1:8000/docs

The SQLite database and its tables are created automatically
when the application is imported. The local database is excluded
from Git.

## Register and log in

1. Open `/docs` and use POST `/register` to create an account:

   ```json
   {
     "username": "exampleuser",
     "password": "example-password-for-learning"
   }
   ```

2. Send the same credentials to POST `/login`.
3. Copy the `access_token` from the login response.
4. Click **Authorize** and enter that token without the `Bearer` prefix.
5. Use the protected book endpoints.

Usernames must contain 3–30 letters, numbers, or underscores.
Passwords must contain 15–128 characters.

For clients such as curl, send the access token in this header:

```http
Authorization: Bearer <access_token>
```

Tokens expire after 30 minutes. Log in again to obtain a new one.

## Endpoints

| Method | Path | Purpose | Token required |
|---|---|---|---|
| POST | `/register` | Register a user | No |
| POST | `/login` | Obtain an access token | No |
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
Database tests use fresh temporary SQLite databases,
keeping local book data untouched. Tests use dummy signing secrets.

The 21 tests cover:

- Password hashing and verification
- JWT creation and decoding
- Missing and invalid tokens
- Successful book creation and retrieval
- Blank-title validation without saving data
- Missing books
- Partial updates and deletion
- Author filtering, pagination, and sorting
- User registration and duplicate usernames
- Successful login, wrong passwords, and unknown usernames
- Rejection of expired and tampered tokens
- Rejection of tokens belonging to deleted users

## Current scope

This is a learning project with registration, login, and JWT authentication.

Books are currently shared. Any authenticated user can create,
update, or delete any book. Per-user ownership and permissions
are not implemented yet.

Logout/token revocation, refresh tokens, and production deployment
are also outside the current implementation.
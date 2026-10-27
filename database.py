import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent / "books.db"

def init_db():
    with sqlite3.connect(DB_PATH) as connection:
        connection.execute("""
            CREATE TABLE IF NOT EXISTS books (
                id INTEGER PRIMARY KEY,
                title TEXT NOT NULL,
                author TEXT NOT NULL
            )
        """)


init_db()

def add_book(title, author):
    with sqlite3.connect(DB_PATH) as connection:
        cursor = connection.execute(
            "INSERT INTO books (title, author) VALUES (?, ?)",
            (title, author)
        )
        return cursor.lastrowid

def get_book(book_id):
    with sqlite3.connect(DB_PATH) as connection:
        connection.row_factory = sqlite3.Row
        row = connection.execute(
            "SELECT id, title, author FROM books WHERE id = ?",
            (book_id,)
        ).fetchone()

        return dict(row) if row is not None else None

def get_all_books(author=None, limit=10, offset=0, sort_by="id"):
    allowed_sorts = {
        "id": "id",
        "title": "title, id"
    }

    order_by = allowed_sorts[sort_by]

    with sqlite3.connect(DB_PATH) as connection:
        connection.row_factory = sqlite3.Row

        if author is None:
            rows = connection.execute(
                f"""
                SELECT id, title, author
                FROM books
                ORDER BY {order_by}
                LIMIT ? OFFSET ?
                """,
                (limit, offset)
            ).fetchall()
        else:
            rows = connection.execute(
                f"""
                SELECT id, title, author
                FROM books
                WHERE author = ?
                ORDER BY {order_by}
                LIMIT ? OFFSET ?
                """,
                (author, limit, offset)
            ).fetchall()

        return [dict(row) for row in rows]

def delete_book(book_id):
    with sqlite3.connect(DB_PATH) as connection:
        cursor = connection.execute(
            "DELETE FROM books WHERE id = ?",
            (book_id,)
        )
        return cursor.rowcount

def update_book(book_id, changes):
    with sqlite3.connect(DB_PATH) as connection:
        if "title" in changes:
            connection.execute(
                "UPDATE books SET title = ? WHERE id = ?",
                (changes["title"], book_id)
            )

        if "author" in changes:
            connection.execute(
                "UPDATE books SET author = ? WHERE id = ?",
                (changes["author"], book_id)
            )

def count_books():
    with sqlite3.connect(DB_PATH) as connection:
        row = connection.execute(
            "SELECT COUNT(*) FROM books"
        ).fetchone()
        return row[0]
    
if __name__ == "__main__":
    print(get_book(1))
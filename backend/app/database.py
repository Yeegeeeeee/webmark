import os
from pathlib import Path
import sqlite3

DATA_DIR = Path(
    os.getenv("WEBMARK_DATA_DIR", Path(__file__).resolve().parent.parent / "data")
)
DATABASE_PATH = DATA_DIR / "webmark.db"
DEFAULT_FOLDER_NAME = "未分类"


class ResultAdapter:
    def __init__(self, cursor):
        self.cursor = cursor

    @property
    def rowcount(self) -> int:
        return self.cursor.rowcount

    def _to_dict(self, row):
        if row is None:
            return None
        columns = [column[0] for column in self.cursor.description]
        return dict(zip(columns, row))

    def fetchone(self):
        return self._to_dict(self.cursor.fetchone())

    def fetchall(self):
        return [self._to_dict(row) for row in self.cursor.fetchall()]


class ConnectionAdapter:
    def __init__(self, connection):
        self.connection = connection

    def execute(self, query: str, parameters: tuple = ()) -> ResultAdapter:
        return ResultAdapter(self.connection.execute(query, parameters))

    def __enter__(self):
        return self

    def __exit__(self, exception_type, exception, traceback):
        try:
            if exception_type is None:
                self.connection.commit()
            else:
                self.connection.rollback()
        finally:
            self.connection.close()


def get_connection() -> ConnectionAdapter:
    database_url = os.getenv("TURSO_DATABASE_URL")
    auth_token = os.getenv("TURSO_AUTH_TOKEN")

    if database_url and auth_token:
        import libsql

        connection = libsql.connect(
            database=database_url,
            auth_token=auth_token,
        )
    else:
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        connection = sqlite3.connect(DATABASE_PATH)
        connection.execute("PRAGMA foreign_keys = ON")

    return ConnectionAdapter(connection)


def initialize_database() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    with get_connection() as connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS folders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
            """
        )

        bookmark_table = connection.execute(
            "SELECT sql FROM sqlite_schema WHERE type = 'table' AND name = 'bookmarks'"
        ).fetchone()

        if bookmark_table is not None and "folder_id" not in bookmark_table["sql"]:
            connection.execute(
                "INSERT OR IGNORE INTO folders (name) VALUES (?)",
                (DEFAULT_FOLDER_NAME,),
            )
            default_folder_id = connection.execute(
                "SELECT id FROM folders WHERE name = ?",
                (DEFAULT_FOLDER_NAME,),
            ).fetchone()["id"]

            connection.execute(
                """
                CREATE TABLE bookmarks_new (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    url TEXT NOT NULL,
                    folder_id INTEGER NOT NULL,
                    title TEXT,
                    markdown TEXT,
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (folder_id) REFERENCES folders(id),
                    UNIQUE (url, folder_id)
                )
                """
            )
            connection.execute(
                """
                INSERT INTO bookmarks_new (
                    id, url, folder_id, title, markdown, created_at, updated_at
                )
                SELECT id, url, ?, title, markdown, created_at, updated_at
                FROM bookmarks
                """,
                (default_folder_id,),
            )
            connection.execute("DROP TABLE bookmarks")
            connection.execute("ALTER TABLE bookmarks_new RENAME TO bookmarks")

        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS bookmarks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                url TEXT NOT NULL,
                folder_id INTEGER NOT NULL,
                title TEXT,
                markdown TEXT,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (folder_id) REFERENCES folders(id),
                UNIQUE (url, folder_id)
            )
            """
        )
        connection.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_bookmarks_folder_id
            ON bookmarks(folder_id)
            """
        )
        connection.execute("PRAGMA optimize")

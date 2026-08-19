from contextlib import asynccontextmanager
import os
from pathlib import Path
import sqlite3
import sys
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup
from fastapi import FastAPI, HTTPException, Response
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field, HttpUrl, field_validator
from trafilatura import extract

from .database import get_connection, initialize_database


class BookmarkRequest(BaseModel):
    url: HttpUrl
    folder: str = Field(min_length=1, max_length=100)

    @field_validator("url", mode="before")
    @classmethod
    def normalize_url(cls, value: str) -> str:
        url = str(value).strip()
        if not url.lower().startswith(("http://", "https://")):
            url = f"https://{url}"
        return url

    @field_validator("folder")
    @classmethod
    def validate_folder(cls, value: str) -> str:
        folder = value.strip()
        if not folder:
            raise ValueError("文件夹名称不能为空")
        return folder


class FolderRequest(BaseModel):
    name: str = Field(min_length=1, max_length=100)

    @field_validator("name")
    @classmethod
    def validate_name(cls, value: str) -> str:
        name = value.strip()
        if not name:
            raise ValueError("文件夹名称不能为空")
        return name


class BookmarkUpdateRequest(BaseModel):
    title: str = Field(min_length=1, max_length=300)
    folder_id: int = Field(gt=0)

    @field_validator("title")
    @classmethod
    def validate_title(cls, value: str) -> str:
        title = value.strip()
        if not title:
            raise ValueError("标题不能为空")
        return title


@asynccontextmanager
async def lifespan(_: FastAPI):
    initialize_database()
    yield


app = FastAPI(title="webmark API", version="0.1.0", lifespan=lifespan)

allowed_origins = ["http://localhost:5173", "http://127.0.0.1:5173"]
if frontend_origin := os.getenv("FRONTEND_ORIGIN"):
    allowed_origins.append(frontend_origin.rstrip("/"))

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_origin_regex=r"https://[a-z0-9-]+\.(?:onrender\.com|vercel\.app)",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/webmark/health")
def health_check() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/webmark/folders")
def get_folders() -> dict[str, str]:
    with get_connection() as connection:
        folders = connection.execute(
            "SELECT id, name FROM folders ORDER BY name"
        ).fetchall()
    return {str(folder["id"]): folder["name"] for folder in folders}


@app.patch("/webmark/folders/{folder_id}", response_class=Response)
def rename_folder(folder_id: int, request_body: FolderRequest):
    try:
        with get_connection() as connection:
            result = connection.execute(
                "UPDATE folders SET name = ? WHERE id = ?",
                (request_body.name, folder_id),
            )
    except sqlite3.IntegrityError as exc:
        raise HTTPException(status_code=409, detail="文件夹名称已存在") from exc

    if result.rowcount == 0:
        raise HTTPException(status_code=404, detail="文件夹不存在")

    return Response(status_code=204)


@app.delete("/webmark/folders/{folder_id}", status_code=204, response_class=Response)
def delete_folder(folder_id: int):
    try:
        with get_connection() as connection:
            result = connection.execute(
                "DELETE FROM folders WHERE id = ?",
                (folder_id,),
            )
    except sqlite3.IntegrityError as exc:
        raise HTTPException(status_code=409, detail="请先删除该文件夹中的收藏") from exc

    if result.rowcount == 0:
        raise HTTPException(status_code=404, detail="文件夹不存在")

    return Response(status_code=204)


def get_page(url: str) -> dict[str, str]:
    parsed_url = urlparse(url)
    if parsed_url.scheme not in {"http", "https"} or not parsed_url.netloc:
        raise HTTPException(status_code=400, detail="请输入有效的 HTTP 或 HTTPS 地址")

    try:
        response = requests.get(
            url,
            timeout=15,
            headers={
                "User-Agent": (
                    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/124.0 Safari/537.36"
                )
            },
        )
        response.raise_for_status()
    except requests.Timeout as exc:
        raise HTTPException(status_code=504, detail="请求网页超时") from exc
    except requests.RequestException as exc:
        raise HTTPException(status_code=502, detail="无法获取该网页") from exc

    content_type = response.headers.get("Content-Type", "")
    if "text/html" not in content_type.lower():
        raise HTTPException(status_code=422, detail="该地址返回的不是 HTML 网页")

    response.encoding = response.apparent_encoding or response.encoding
    soup = BeautifulSoup(response.text, "html.parser")

    title = soup.title.get_text(" ", strip=True) if soup.title else ""
    if not title:
        heading = soup.find("h1")
        title = heading.get_text(" ", strip=True) if heading else str(response.url)

    content = extract(
        response.text,
        url=str(response.url),
        output_format="markdown",
        include_links=True,
        include_images=True,
        include_tables=True,
        favor_precision=True,
    )
    if not content:
        raise HTTPException(status_code=422, detail="无法从该网页提取正文")

    return {
        "url": str(response.url),
        "title": title,
        "content": content,
    }


@app.get("/webmark/bookmarks")
def get_bookmarks(
    folder_id: int | None = None,
    keyword: str | None = None,
) -> list[dict]:
    with get_connection() as connection:
        query = """
            SELECT
                bookmarks.id,
                bookmarks.url,
                bookmarks.folder_id,
                folders.name AS folder_name,
                bookmarks.title,
                bookmarks.markdown,
                bookmarks.created_at,
                bookmarks.updated_at
            FROM bookmarks
            JOIN folders ON folders.id = bookmarks.folder_id
        """
        conditions: list[str] = []
        parameters: list = []
        if folder_id is not None:
            conditions.append("bookmarks.folder_id = ?")
            parameters.append(folder_id)
        if keyword and keyword.strip():
            escaped_keyword = (
                keyword.strip()
                .replace("\\", "\\\\")
                .replace("%", "\\%")
                .replace("_", "\\_")
            )
            pattern = f"%{escaped_keyword}%"
            conditions.append(
                """
                (
                    bookmarks.title LIKE ? ESCAPE '\\'
                    OR bookmarks.url LIKE ? ESCAPE '\\'
                    OR bookmarks.markdown LIKE ? ESCAPE '\\'
                    OR folders.name LIKE ? ESCAPE '\\'
                )
                """
            )
            parameters.extend([pattern, pattern, pattern, pattern])
        if conditions:
            query += " WHERE " + " AND ".join(conditions)
        query += " ORDER BY bookmarks.created_at DESC, bookmarks.id DESC"

        bookmarks = connection.execute(query, tuple(parameters)).fetchall()

    return [
        {
            "id": bookmark["id"],
            "url": bookmark["url"],
            "folder_id": bookmark["folder_id"],
            "folder_name": bookmark["folder_name"],
            "title": bookmark["title"],
            "content": bookmark["markdown"],
            "created_at": bookmark["created_at"],
            "updated_at": bookmark["updated_at"],
        }
        for bookmark in bookmarks
    ]


@app.get("/webmark/bookmarks/{bookmark_id}")
def get_bookmark(bookmark_id: int) -> dict:
    with get_connection() as connection:
        bookmark = connection.execute(
            """
            SELECT
                bookmarks.id,
                bookmarks.url,
                bookmarks.folder_id,
                folders.name AS folder_name,
                bookmarks.title,
                bookmarks.markdown,
                bookmarks.created_at,
                bookmarks.updated_at
            FROM bookmarks
            JOIN folders ON folders.id = bookmarks.folder_id
            WHERE bookmarks.id = ?
            """,
            (bookmark_id,),
        ).fetchone()

    if bookmark is None:
        raise HTTPException(status_code=404, detail="收藏不存在")

    return {
        "id": bookmark["id"],
        "url": bookmark["url"],
        "folder_id": bookmark["folder_id"],
        "folder_name": bookmark["folder_name"],
        "title": bookmark["title"],
        "content": bookmark["markdown"],
        "created_at": bookmark["created_at"],
        "updated_at": bookmark["updated_at"],
    }


@app.patch("/webmark/bookmarks/{bookmark_id}", response_class=Response)
def update_bookmark(bookmark_id: int, request_body: BookmarkUpdateRequest):
    try:
        with get_connection() as connection:
            folder = connection.execute(
                "SELECT id FROM folders WHERE id = ?",
                (request_body.folder_id,),
            ).fetchone()
            if folder is None:
                raise HTTPException(status_code=404, detail="文件夹不存在")

            result = connection.execute(
                """
                UPDATE bookmarks
                SET title = ?, folder_id = ?, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
                """,
                (request_body.title, request_body.folder_id, bookmark_id),
            )
    except sqlite3.IntegrityError as exc:
        raise HTTPException(status_code=409, detail="该网址已存在于目标文件夹") from exc

    if result.rowcount == 0:
        raise HTTPException(status_code=404, detail="收藏不存在")

    return Response(status_code=204)


def save_bookmarks(page: dict[str, str], folder_name: str) -> None:
    try:
        with get_connection() as connection:
            connection.execute(
                "INSERT OR IGNORE INTO folders (name) VALUES (?)",
                (folder_name,),
            )
            folder = connection.execute(
                "SELECT id FROM folders WHERE name = ?",
                (folder_name,),
            ).fetchone()

            connection.execute(
                """
                INSERT INTO bookmarks (url, folder_id, title, markdown)
                VALUES (?, ?, ?, ?)
                """,
                (page["url"], folder["id"], page["title"], page["content"]),
            )
    except sqlite3.IntegrityError as exc:
        raise HTTPException(status_code=409, detail="该网址已收藏到这个文件夹") from exc
    except sqlite3.DatabaseError as exc:
        raise HTTPException(status_code=500, detail="收藏保存失败") from exc


@app.delete(
    "/webmark/bookmarks/{bookmark_id}",
    status_code=204,
    response_class=Response,
)
def delete_bookmarks(bookmark_id: int):
    with get_connection() as connection:
        result = connection.execute(
            "DELETE FROM bookmarks WHERE id = ?",
            (bookmark_id,),
        )

    if result.rowcount == 0:
        raise HTTPException(status_code=404, detail="收藏不存在")

    return Response(status_code=204)


@app.post("/webmark/bookmarks", status_code=201, response_class=Response)
def create_bookmarks(request_body: BookmarkRequest):
    page = get_page(str(request_body.url))
    save_bookmarks(page, request_body.folder)
    return Response(status_code=201)


def frontend_directory() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys._MEIPASS) / "frontend_dist"
    return Path(__file__).resolve().parents[2] / "frontend" / "dist"


FRONTEND_DIRECTORY = frontend_directory()
if FRONTEND_DIRECTORY.is_dir():
    assets_directory = FRONTEND_DIRECTORY / "assets"
    if assets_directory.is_dir():
        app.mount("/assets", StaticFiles(directory=assets_directory), name="assets")

    @app.get("/{path:path}", include_in_schema=False)
    def serve_frontend(path: str):
        requested_file = (FRONTEND_DIRECTORY / path).resolve()
        if (
            path
            and requested_file.is_file()
            and FRONTEND_DIRECTORY.resolve() in requested_file.parents
        ):
            return FileResponse(requested_file)
        return FileResponse(FRONTEND_DIRECTORY / "index.html")

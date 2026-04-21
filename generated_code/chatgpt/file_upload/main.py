import os
import shutil
import sqlite3
import uuid
from datetime import datetime
from contextlib import closing

from fastapi import FastAPI, File, Form, HTTPException, UploadFile, status
from fastapi.responses import FileResponse
from pydantic import BaseModel

app = FastAPI(title="FastAPI File Upload App")

DATABASE_NAME = "uploads.db"
UPLOAD_DIR = "uploads"

ALLOWED_AVATAR_EXTENSIONS = {".jpg", ".jpeg", ".png"}
ALLOWED_DOCUMENT_EXTENSIONS = {".pdf", ".docx"}


class UploadMetadata(BaseModel):
    id: int
    original_filename: str
    stored_filename: str
    file_type: str
    uploaded_by: str
    upload_time: str


def get_db_connection():
    conn = sqlite3.connect(DATABASE_NAME)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    os.makedirs(UPLOAD_DIR, exist_ok=True)

    with closing(get_db_connection()) as conn:
        with conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS uploads (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    original_filename TEXT NOT NULL,
                    stored_filename TEXT NOT NULL UNIQUE,
                    file_type TEXT NOT NULL,
                    uploaded_by TEXT NOT NULL,
                    upload_time TEXT NOT NULL
                )
                """
            )


@app.on_event("startup")
def startup():
    init_db()


def get_extension(filename: str) -> str:
    return os.path.splitext(filename)[1].lower()


def generate_stored_filename(original_filename: str) -> str:
    ext = get_extension(original_filename)
    return f"{uuid.uuid4().hex}{ext}"


def save_upload_metadata(
    original_filename: str,
    stored_filename: str,
    file_type: str,
    uploaded_by: str,
):
    upload_time = datetime.utcnow().isoformat()

    with closing(get_db_connection()) as conn:
        with conn:
            cursor = conn.execute(
                """
                INSERT INTO uploads (
                    original_filename,
                    stored_filename,
                    file_type,
                    uploaded_by,
                    upload_time
                )
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    original_filename,
                    stored_filename,
                    file_type,
                    uploaded_by,
                    upload_time,
                ),
            )
            return {
                "id": cursor.lastrowid,
                "original_filename": original_filename,
                "stored_filename": stored_filename,
                "file_type": file_type,
                "uploaded_by": uploaded_by,
                "upload_time": upload_time,
            }


def save_file(upload_file: UploadFile, stored_filename: str) -> str:
    file_path = os.path.join(UPLOAD_DIR, stored_filename)
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(upload_file.file, buffer)
    return file_path


@app.get("/")
def home():
    return {"message": "FastAPI file upload app is running."}


@app.post("/upload/avatar", status_code=status.HTTP_201_CREATED)
def upload_avatar(
    uploaded_by: str = Form(...),
    file: UploadFile = File(...),
):
    extension = get_extension(file.filename)

    if extension not in ALLOWED_AVATAR_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only JPG and PNG files are allowed for avatars.",
        )

    stored_filename = generate_stored_filename(file.filename)
    file_path = save_file(file, stored_filename)

    metadata = save_upload_metadata(
        original_filename=file.filename,
        stored_filename=stored_filename,
        file_type="avatar",
        uploaded_by=uploaded_by,
    )

    return {
        "message": "Avatar uploaded successfully.",
        "file_path": file_path,
        "file_url": f"/files/{stored_filename}",
        "metadata": metadata,
    }


@app.post("/upload/document", status_code=status.HTTP_201_CREATED)
def upload_document(
    uploaded_by: str = Form(...),
    file: UploadFile = File(...),
):
    extension = get_extension(file.filename)

    if extension not in ALLOWED_DOCUMENT_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only PDF and DOCX files are allowed for documents.",
        )

    stored_filename = generate_stored_filename(file.filename)
    file_path = save_file(file, stored_filename)

    metadata = save_upload_metadata(
        original_filename=file.filename,
        stored_filename=stored_filename,
        file_type="document",
        uploaded_by=uploaded_by,
    )

    return {
        "message": "Document uploaded successfully.",
        "file_path": file_path,
        "file_url": f"/files/{stored_filename}",
        "metadata": metadata,
    }


@app.get("/files/{filename}")
def get_uploaded_file(filename: str):
    file_path = os.path.join(UPLOAD_DIR, filename)

    if not os.path.exists(file_path):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File not found.",
        )

    return FileResponse(path=file_path, filename=filename)


@app.get("/uploads")
def list_uploads():
    with closing(get_db_connection()) as conn:
        rows = conn.execute(
            """
            SELECT id, original_filename, stored_filename, file_type, uploaded_by, upload_time
            FROM uploads
            ORDER BY id DESC
            """
        ).fetchall()

    return {
        "uploads": [dict(row) for row in rows]
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
    
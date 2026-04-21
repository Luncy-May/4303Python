from fastapi import FastAPI, UploadFile, File, HTTPException, Depends
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
import sqlite3
import os
import shutil
from pathlib import Path
from datetime import datetime
from typing import Optional

app = FastAPI(title="File Upload API")

# Configuration
UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)
AVATAR_DIR = UPLOAD_DIR / "avatars"
DOCUMENT_DIR = UPLOAD_DIR / "documents"
AVATAR_DIR.mkdir(exist_ok=True)
DOCUMENT_DIR.mkdir(exist_ok=True)

DB_PATH = "uploads/file_metadata.db"
ALLOWED_IMAGE_TYPES = {"image/jpeg", "image/png"}
ALLOWED_DOCUMENT_TYPES = {"application/pdf", "application/vnd.openxmlformats-officedocument.wordprocessingml.document"}
MAX_IMAGE_SIZE = 5 * 1024 * 1024  # 5MB
MAX_DOCUMENT_SIZE = 20 * 1024 * 1024  # 20MB

# Serve uploaded files statically
app.mount("/files", StaticFiles(directory="uploads"), name="files")


def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS file_metadata (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            filename TEXT NOT NULL,
            original_filename TEXT NOT NULL,
            file_type TEXT NOT NULL,
            upload_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            user_id TEXT,
            file_path TEXT NOT NULL,
            file_size INTEGER
        )
    ''')
    conn.commit()
    conn.close()


def get_db():
    init_db()
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def validate_and_save_file(
    file: UploadFile,
    allowed_types: set,
    max_size: int,
    upload_directory: Path,
    user_id: Optional[str] = None
) -> dict:
    if file.content_type not in allowed_types:
        raise HTTPException(status_code=400, detail=f"Invalid file type. Allowed: {allowed_types}")

    file_size = len(file.file.read())
    file.file.seek(0)

    if file_size > max_size:
        raise HTTPException(status_code=413, detail=f"File too large. Max size: {max_size / 1024 / 1024}MB")

    # Generate unique filename
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_")
    safe_filename = "".join(c for c in file.filename if c.isalnum() or c in "._-")
    unique_filename = timestamp + safe_filename

    file_path = upload_directory / unique_filename

    with open(file_path, "wb") as f:
        shutil.copyfileobj(file.file, f)

    # Store in database
    conn = get_db()
    c = conn.cursor()
    relative_path = str(file_path.relative_to(UPLOAD_DIR))

    c.execute('''
        INSERT INTO file_metadata
        (filename, original_filename, file_type, user_id, file_path, file_size)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (unique_filename, file.filename, file.content_type, user_id, relative_path, file_size))

    conn.commit()
    conn.close()

    return {
        "filename": unique_filename,
        "original_filename": file.filename,
        "file_path": relative_path,
        "url": f"/files/{relative_path}",
        "size": file_size,
        "upload_time": datetime.now().isoformat()
    }


@app.post("/upload/avatar")
async def upload_avatar(file: UploadFile = File(...), user_id: Optional[str] = None):
    """Upload a profile picture (JPG, PNG)"""
    result = validate_and_save_file(
        file,
        ALLOWED_IMAGE_TYPES,
        MAX_IMAGE_SIZE,
        AVATAR_DIR,
        user_id
    )
    return {
        "message": "Avatar uploaded successfully",
        "data": result
    }


@app.post("/upload/document")
async def upload_document(file: UploadFile = File(...), user_id: Optional[str] = None):
    """Upload a document (PDF, DOCX)"""
    result = validate_and_save_file(
        file,
        ALLOWED_DOCUMENT_TYPES,
        MAX_DOCUMENT_SIZE,
        DOCUMENT_DIR,
        user_id
    )
    return {
        "message": "Document uploaded successfully",
        "data": result
    }


@app.get("/files/{file_path:path}")
async def download_file(file_path: str):
    """Download a file by its path"""
    full_path = UPLOAD_DIR / file_path

    if not full_path.exists() or not full_path.is_file():
        raise HTTPException(status_code=404, detail="File not found")

    if not str(full_path.resolve()).startswith(str(UPLOAD_DIR.resolve())):
        raise HTTPException(status_code=403, detail="Access denied")

    return FileResponse(full_path)


@app.get("/metadata")
async def get_metadata(user_id: Optional[str] = None, file_type: Optional[str] = None):
    """Retrieve file metadata with optional filters"""
    conn = get_db()
    c = conn.cursor()

    query = "SELECT * FROM file_metadata WHERE 1=1"
    params = []

    if user_id:
        query += " AND user_id = ?"
        params.append(user_id)

    if file_type:
        query += " AND file_type LIKE ?"
        params.append(f"%{file_type}%")

    query += " ORDER BY upload_time DESC"

    c.execute(query, params)
    rows = c.fetchall()
    conn.close()

    return {
        "count": len(rows),
        "files": [dict(row) for row in rows]
    }


@app.delete("/files/{file_id}")
async def delete_file(file_id: int):
    """Delete a file by its database ID"""
    conn = get_db()
    c = conn.cursor()

    c.execute("SELECT file_path FROM file_metadata WHERE id = ?", (file_id,))
    row = c.fetchone()

    if not row:
        conn.close()
        raise HTTPException(status_code=404, detail="File not found in database")

    file_path = UPLOAD_DIR / row["file_path"]

    try:
        if file_path.exists():
            file_path.unlink()
    except Exception as e:
        conn.close()
        raise HTTPException(status_code=500, detail=f"Failed to delete file: {str(e)}")

    c.execute("DELETE FROM file_metadata WHERE id = ?", (file_id,))
    conn.commit()
    conn.close()

    return {"message": "File deleted successfully", "file_id": file_id}


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "ok"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

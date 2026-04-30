import sqlite3
import os
import shutil
from datetime import datetime
from fastapi import FastAPI, HTTPException, Depends, status, Request, Response, File, UploadFile
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import Optional, List
import uuid

app = FastAPI()

# Constants
UPLOAD_DIR = "uploads"
AVATAR_DIR = os.path.join(UPLOAD_DIR, "avatars")
DOCUMENT_DIR = os.path.join(UPLOAD_DIR, "documents")

# Ensure upload directories exist
os.makedirs(AVATAR_DIR, exist_ok=True)
os.makedirs(DOCUMENT_DIR, exist_ok=True)

# Mount the uploads directory to serve files
app.mount("/static", StaticFiles(directory=UPLOAD_DIR), name="static")

# Database setup
def init_db():
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS file_metadata (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            filename TEXT NOT NULL,
            original_filename TEXT NOT NULL,
            file_path TEXT NOT NULL,
            upload_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            uploader_username TEXT NOT NULL,
            file_type TEXT NOT NULL
        )
    ''')
    conn.commit()
    conn.close()

init_db()

# In-memory session store (In a real app, use Redis or a database)
sessions = {}

# Pydantic models
class User(BaseModel):
    username: str
    password: str

class UserResponse(BaseModel):
    username: str

# Helper functions
def get_db_connection():
    conn = sqlite3.connect('users.db')
    conn.row_factory = sqlite3.Row
    return conn

def get_current_user(request: Request):
    session_id = request.cookies.get("session_id")
    if not session_id or session_id not in sessions:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
        )
    return sessions[session_id]

@app.post("/register", status_code=status.HTTP_201_CREATED)
async def register(user: User):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO users (username, password) VALUES (?, ?)", (user.username, user.password))
        conn.commit()
    except sqlite3.IntegrityError:
        raise HTTPException(status_code=400, detail="Username already registered")
    finally:
        conn.close()
    return {"message": "User registered successfully"}

@app.post("/login")
async def login(user: User, response: Response):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE username = ? AND password = ?", (user.username, user.password))
    db_user = cursor.fetchone()
    conn.close()

    if not db_user:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    session_id = str(uuid.uuid4())
    sessions[session_id] = db_user["username"]
    response.set_cookie(key="session_id", value=session_id, httponly=True)
    
    return {"message": "Login successful"}

@app.get("/dashboard")
async def dashboard(username: str = Depends(get_current_user)):
    return {"message": f"Welcome to your dashboard, {username}!"}

@app.post("/logout")
async def logout(request: Request, response: Response):
    session_id = request.cookies.get("session_id")
    if session_id in sessions:
        del sessions[session_id]
    response.delete_cookie("session_id")
    return {"message": "Logged out successfully"}

# File Upload Endpoints
@app.post("/upload/avatar")
async def upload_avatar(
    file: UploadFile = File(...),
    username: str = Depends(get_current_user)
):
    # Validate file type
    if not file.content_type in ["image/jpeg", "image/png"]:
        raise HTTPException(status_code=400, detail="Only JPG and PNG images are allowed for avatars")

    return await save_file(file, AVATAR_DIR, username, "avatar")

@app.post("/upload/document")
async def upload_document(
    file: UploadFile = File(...),
    username: str = Depends(get_current_user)
):
    # Validate file type
    allowed_types = [
        "application/pdf",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document", # docx
        "application/msword" # doc
    ]
    if not file.content_type in allowed_types:
        raise HTTPException(status_code=400, detail="Only PDF and DOCX documents are allowed")

    return await save_file(file, DOCUMENT_DIR, username, "document")

async def save_file(file: UploadFile, directory: str, username: str, file_type: str):
    # Create a unique filename to avoid collisions
    unique_filename = f"{uuid.uuid4()}_{file.filename}"
    file_path = os.path.join(directory, unique_filename)

    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Could not save file: {str(e)}")

    # Store metadata in database
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO file_metadata (filename, original_filename, file_path, uploader_username, file_type) VALUES (?, ?, ?, ?, ?)",
        (unique_filename, file.filename, file_path, username, file_type)
    )
    conn.commit()
    conn.close()

    # Create a relative URL for the file
    relative_path = os.path.relpath(file_path, UPLOAD_DIR).replace("\\", "/")
    file_url = f"/static/{relative_path}"

    return {
        "filename": unique_filename,
        "original_filename": file.filename,
        "url": file_url,
        "message": "File uploaded successfully"
    }

@app.get("/files/{filename}")
async def get_file_by_name(filename: str):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT file_path FROM file_metadata WHERE filename = ?", (filename,))
    row = cursor.fetchone()
    conn.close()

    if not row:
        raise HTTPException(status_code=404, detail="File not found")

    file_path = row["file_path"]
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="File file not found on disk")

    return FileResponse(file_path)

@app.get("/my-files")
async def list_my_files(username: str = Depends(get_current_user)):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM file_metadata WHERE uploader_username = ?", (username,))
    files = cursor.fetchall()
    conn.close()

    return [dict(file) for file in files]

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

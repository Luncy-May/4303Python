import sqlite3
import uuid
import hashlib
from datetime import datetime, timedelta
from typing import Optional

from fastapi import FastAPI, HTTPException, Depends, Cookie, Response
from pydantic import BaseModel

app = FastAPI()

DB_PATH = "users.db"
sessions: dict[str, dict] = {}  # session_token -> {username, expires_at}
SESSION_DURATION_HOURS = 24


# --- Database Setup ---

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()


def setup_database():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id       INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT    NOT NULL UNIQUE,
            password TEXT    NOT NULL
        )
    """)
    conn.commit()
    conn.close()


# --- Helpers ---

def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()


def create_session(username: str) -> str:
    token = str(uuid.uuid4())
    sessions[token] = {
        "username": username,
        "expires_at": datetime.utcnow() + timedelta(hours=SESSION_DURATION_HOURS),
    }
    return token


def get_current_user(session_token: Optional[str] = Cookie(default=None)) -> str:
    if not session_token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    session = sessions.get(session_token)
    if not session:
        raise HTTPException(status_code=401, detail="Invalid session")
    if datetime.utcnow() > session["expires_at"]:
        sessions.pop(session_token, None)
        raise HTTPException(status_code=401, detail="Session expired")
    return session["username"]


# --- Schemas ---

class UserCredentials(BaseModel):
    username: str
    password: str


# --- Startup ---

@app.on_event("startup")
def on_startup():
    setup_database()


# --- Routes ---

@app.post("/register", status_code=201)
def register(credentials: UserCredentials, db: sqlite3.Connection = Depends(get_db)):
    username = credentials.username.strip()
    password = credentials.password

    if not username or not password:
        raise HTTPException(status_code=400, detail="Username and password are required")

    hashed = hash_password(password)
    try:
        db.execute(
            "INSERT INTO users (username, password) VALUES (?, ?)",
            (username, hashed),
        )
        db.commit()
    except sqlite3.IntegrityError:
        raise HTTPException(status_code=409, detail="Username already taken")

    return {"message": "User registered successfully"}


@app.post("/login")
def login(credentials: UserCredentials, response: Response, db: sqlite3.Connection = Depends(get_db)):
    username = credentials.username.strip()
    hashed = hash_password(credentials.password)

    row = db.execute(
        "SELECT id FROM users WHERE username = ? AND password = ?",
        (username, hashed),
    ).fetchone()

    if not row:
        raise HTTPException(status_code=401, detail="Invalid username or password")

    token = create_session(username)
    response.set_cookie(
        key="session_token",
        value=token,
        httponly=True,
        max_age=SESSION_DURATION_HOURS * 3600,
        samesite="lax",
    )
    return {"message": "Login successful"}


@app.get("/dashboard")
def dashboard(current_user: str = Depends(get_current_user)):
    return {"message": f"Welcome to your dashboard, {current_user}!"}


@app.post("/logout")
def logout(response: Response, session_token: Optional[str] = Cookie(default=None)):
    if session_token:
        sessions.pop(session_token, None)
    response.delete_cookie("session_token")
    return {"message": "Logged out successfully"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("login_system_sonnet:app", host="0.0.0.0", port=8000, reload=True)

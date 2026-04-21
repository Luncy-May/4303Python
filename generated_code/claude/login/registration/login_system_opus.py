import sqlite3
import hashlib
import secrets
from datetime import datetime, timedelta
from contextlib import contextmanager

from fastapi import FastAPI, HTTPException, Depends, Request, Response
from fastapi.security import APIKeyCookie
from pydantic import BaseModel

app = FastAPI(title="User Auth System")

DATABASE = "users.db"
SESSION_EXPIRY_HOURS = 24

# In-memory session store
active_sessions: dict[str, dict] = {}

cookie_scheme = APIKeyCookie(name="session_id", auto_error=False)


# ── Database ────────────────────────────────────────────────────────

@contextmanager
def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()


def setup_database():
    with get_db() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL UNIQUE,
                password TEXT NOT NULL
            )
            """
        )
        conn.commit()


# ── Helpers ─────────────────────────────────────────────────────────

def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode("utf-8")).hexdigest()


def verify_user(username: str, password: str) -> bool:
    with get_db() as conn:
        row = conn.execute(
            "SELECT password FROM users WHERE username = ?", (username,)
        ).fetchone()
    if row is None:
        return False
    return row["password"] == hash_password(password)


def create_session(username: str) -> str:
    token = secrets.token_hex(32)
    active_sessions[token] = {
        "username": username,
        "expires": datetime.utcnow() + timedelta(hours=SESSION_EXPIRY_HOURS),
    }
    return token


def get_current_user(session_id: str | None = Depends(cookie_scheme)) -> str:
    if session_id is None:
        raise HTTPException(status_code=401, detail="Not authenticated")

    session = active_sessions.get(session_id)
    if session is None:
        raise HTTPException(status_code=401, detail="Invalid session")

    if datetime.utcnow() > session["expires"]:
        active_sessions.pop(session_id, None)
        raise HTTPException(status_code=401, detail="Session expired")

    return session["username"]


# ── Schemas ─────────────────────────────────────────────────────────

class Credentials(BaseModel):
    username: str
    password: str


# ── Lifecycle ───────────────────────────────────────────────────────

@app.on_event("startup")
def startup():
    setup_database()


# ── Endpoints ───────────────────────────────────────────────────────

@app.post("/register")
def register(creds: Credentials):
    hashed = hash_password(creds.password)
    with get_db() as conn:
        try:
            conn.execute(
                "INSERT INTO users (username, password) VALUES (?, ?)",
                (creds.username, hashed),
            )
            conn.commit()
        except sqlite3.IntegrityError:
            raise HTTPException(status_code=400, detail="Username already exists")
    return {"message": "Registration successful"}


@app.post("/login")
def login(creds: Credentials, response: Response):
    if not verify_user(creds.username, creds.password):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    token = create_session(creds.username)
    response.set_cookie(
        key="session_id",
        value=token,
        httponly=True,
        max_age=SESSION_EXPIRY_HOURS * 3600,
    )
    return {"message": "Login successful"}


@app.get("/dashboard")
def dashboard(username: str = Depends(get_current_user)):
    return {"message": f"Welcome, {username}!"}


@app.post("/logout")
def logout(response: Response, session_id: str | None = Depends(cookie_scheme)):
    if session_id and session_id in active_sessions:
        del active_sessions[session_id]
    response.delete_cookie("session_id")
    return {"message": "Logged out"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("login_system_opus:app", host="0.0.0.0", port=8000, reload=True)

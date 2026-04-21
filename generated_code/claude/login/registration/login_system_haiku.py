import sqlite3
import hashlib
import secrets
from datetime import datetime, timedelta
from fastapi import FastAPI, HTTPException, Depends, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import os

app = FastAPI()

# Database configuration
DATABASE_PATH = "users.db"
SESSIONS = {}  # Simple in-memory session store: {session_token: {"username": str, "expires": datetime}}
SESSION_TIMEOUT = 24  # hours

# Models
class UserRegister(BaseModel):
    username: str
    password: str

class UserLogin(BaseModel):
    username: str
    password: str

class LoginResponse(BaseModel):
    message: str
    session_token: str = None

# Database setup
def init_db():
    """Initialize the database with a users table."""
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()

def hash_password(password: str) -> str:
    """Hash a password using SHA256."""
    return hashlib.sha256(password.encode()).hexdigest()

def verify_password(password: str, password_hash: str) -> bool:
    """Verify a password against its hash."""
    return hash_password(password) == password_hash

def create_session(username: str) -> str:
    """Create a new session token for a user."""
    session_token = secrets.token_urlsafe(32)
    SESSIONS[session_token] = {
        "username": username,
        "expires": datetime.utcnow() + timedelta(hours=SESSION_TIMEOUT)
    }
    return session_token

def get_current_user(request: Request) -> str:
    """Extract and validate the current user from the session token."""
    # Try to get token from cookie or Authorization header
    token = request.cookies.get("session_token")
    if not token:
        auth_header = request.headers.get("Authorization", "")
        if auth_header.startswith("Bearer "):
            token = auth_header[7:]

    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated")

    session = SESSIONS.get(token)
    if not session:
        raise HTTPException(status_code=401, detail="Invalid or expired session")

    if datetime.utcnow() > session["expires"]:
        del SESSIONS[token]
        raise HTTPException(status_code=401, detail="Session expired")

    return session["username"]

# Endpoints
@app.on_event("startup")
async def startup():
    """Initialize the database on startup."""
    init_db()

@app.post("/register", response_model=dict)
async def register(user: UserRegister):
    """Register a new user."""
    if len(user.username) < 3:
        raise HTTPException(status_code=400, detail="Username must be at least 3 characters")
    if len(user.password) < 6:
        raise HTTPException(status_code=400, detail="Password must be at least 6 characters")

    password_hash = hash_password(user.password)

    try:
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO users (username, password_hash) VALUES (?, ?)",
            (user.username, password_hash)
        )
        conn.commit()
        conn.close()
        return {"message": "User registered successfully"}
    except sqlite3.IntegrityError:
        raise HTTPException(status_code=400, detail="Username already exists")

@app.post("/login", response_model=LoginResponse)
async def login(user: UserLogin):
    """Authenticate a user and create a session."""
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    cursor.execute(
        "SELECT password_hash FROM users WHERE username = ?",
        (user.username,)
    )
    result = cursor.fetchone()
    conn.close()

    if not result or not verify_password(user.password, result[0]):
        raise HTTPException(status_code=401, detail="Invalid username or password")

    session_token = create_session(user.username)

    response = JSONResponse(
        content={"message": "Login successful", "session_token": session_token},
        status_code=200
    )
    response.set_cookie("session_token", session_token, httponly=True, max_age=SESSION_TIMEOUT * 3600)
    return response

@app.get("/dashboard")
async def dashboard(current_user: str = Depends(get_current_user)):
    """Protected endpoint that requires authentication."""
    return {"message": f"Welcome, {current_user}!"}

@app.post("/logout")
async def logout(request: Request):
    """Logout by clearing the session."""
    token = request.cookies.get("session_token")
    if token and token in SESSIONS:
        del SESSIONS[token]

    response = JSONResponse(
        content={"message": "Logged out successfully"},
        status_code=200
    )
    response.delete_cookie("session_token")
    return response

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

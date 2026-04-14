# Assembled FastAPI app from ChatGPT-generated code
# Paste generated_code/chatgpt/*.py components here

from fastapi import FastAPI

app = FastAPI()

# TODO: integrate generated endpoints
import os
import sqlite3
import hashlib
import secrets
from contextlib import closing

from fastapi import FastAPI, HTTPException, Request, status
from pydantic import BaseModel, Field
from starlette.middleware.sessions import SessionMiddleware

app = FastAPI(title="ChatGPT Generated Login App")

DATABASE_NAME = "users.db"
SESSION_SECRET = os.getenv("SESSION_SECRET", "change-this-in-production")


class UserCredentials(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=6, max_length=128)


def get_db_connection():
    conn = sqlite3.connect(DATABASE_NAME)
    conn.row_factory = sqlite3.Row
    return conn


def hash_password(password: str, salt: str) -> str:
    hashed = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt.encode("utf-8"),
        100_000,
    )
    return hashed.hex()


def create_password_record(password: str):
    salt = secrets.token_hex(16)
    password_hash = hash_password(password, salt)
    return salt, password_hash


def verify_password(password: str, salt: str, stored_hash: str) -> bool:
    return hash_password(password, salt) == stored_hash


def init_db():
    with closing(get_db_connection()) as conn:
        with conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT NOT NULL UNIQUE,
                    password_hash TEXT NOT NULL,
                    salt TEXT NOT NULL
                )
                """
            )


@app.on_event("startup")
def startup():
    init_db()


app.add_middleware(
    SessionMiddleware,
    secret_key=SESSION_SECRET,
    session_cookie="session",
    max_age=60 * 60 * 24,
    same_site="lax",
    https_only=False,
)


@app.get("/")
def home():
    return {"message": "FastAPI login system is running."}


@app.post("/register", status_code=status.HTTP_201_CREATED)
def register(user: UserCredentials):
    salt, password_hash = create_password_record(user.password)

    try:
        with closing(get_db_connection()) as conn:
            with conn:
                conn.execute(
                    """
                    INSERT INTO users (username, password_hash, salt)
                    VALUES (?, ?, ?)
                    """,
                    (user.username, password_hash, salt),
                )
    except sqlite3.IntegrityError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already exists.",
        )

    return {"message": "User registered successfully."}


@app.post("/login")
def login(user: UserCredentials, request: Request):
    with closing(get_db_connection()) as conn:
        row = conn.execute(
            """
            SELECT id, username, password_hash, salt
            FROM users
            WHERE username = ?
            """,
            (user.username,),
        ).fetchone()

    if row is None or not verify_password(user.password, row["salt"], row["password_hash"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password.",
        )

    request.session["user_id"] = row["id"]
    request.session["username"] = row["username"]

    return {"message": "Login successful."}


@app.post("/logout")
def logout(request: Request):
    request.session.clear()
    return {"message": "Logged out successfully."}


@app.get("/dashboard")
def dashboard(request: Request):
    username = request.session.get("username")
    if not username:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="You must be logged in to access the dashboard.",
        )

    return {"message": f"Welcome to your dashboard, {username}."}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
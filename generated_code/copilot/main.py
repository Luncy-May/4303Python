import sqlite3
from fastapi import FastAPI, HTTPException, Depends, status, Request, Response
from pydantic import BaseModel
from typing import Optional
import uuid

app = FastAPI()

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

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

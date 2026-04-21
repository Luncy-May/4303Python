import sqlite3
from contextlib import closing

from fastapi import FastAPI, HTTPException, Query

app = FastAPI(title="FastAPI Product Search App")

DATABASE_NAME = "products.db"


def get_db_connection():
    conn = sqlite3.connect(DATABASE_NAME)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    with closing(get_db_connection()) as conn:
        with conn:
            # Create the products table
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS products (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    description TEXT NOT NULL,
                    price REAL NOT NULL
                )
                """
            )

            # Add sample data if the table is empty
            count = conn.execute("SELECT COUNT(*) FROM products").fetchone()[0]
            if count == 0:
                sample_products = [
                    ("Laptop", "Lightweight laptop for school and work", 899.99),
                    ("Headphones", "Noise-cancelling over-ear headphones", 199.99),
                    ("Coffee Mug", "Ceramic mug for hot and cold drinks", 12.50),
                    ("Notebook", "Lined notebook for class notes", 5.99),
                    ("Phone Charger", "Fast USB-C wall charger", 24.99),
                ]
                conn.executemany(
                    """
                    INSERT INTO products (name, description, price)
                    VALUES (?, ?, ?)
                    """,
                    sample_products,
                )


@app.on_event("startup")
def startup():
    init_db()


@app.get("/")
def home():
    return {"message": "FastAPI product search app is running."}


@app.get("/search")
def search_products(q: str = Query(..., description="Search term")):
    if not q.strip():
        raise HTTPException(status_code=400, detail="Query cannot be empty.")

    with closing(get_db_connection()) as conn:
        # Search product names and descriptions
        rows = conn.execute(
            """
            SELECT id, name, description, price
            FROM products
            WHERE name LIKE ? OR description LIKE ?
            """,
            (f"%{q}%", f"%{q}%"),
        ).fetchall()

    return {
        "query": q,
        "results": [dict(row) for row in rows],
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)

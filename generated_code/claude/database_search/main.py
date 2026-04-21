import sqlite3
import os
from contextlib import contextmanager
from fastapi import FastAPI, Query
from fastapi.responses import JSONResponse

DATABASE_PATH = "products.db"

app = FastAPI()


@contextmanager
def get_db_connection():
    """Context manager for database connections."""
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()


def setup_database():
    """Initialize the database with products table and sample data."""
    with get_db_connection() as conn:
        cursor = conn.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS products (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                description TEXT,
                price REAL NOT NULL,
                stock INTEGER DEFAULT 0
            )
        """)

        cursor.execute("SELECT COUNT(*) FROM products")
        if cursor.fetchone()[0] == 0:
            sample_products = [
                ("Wireless Headphones", "High-quality Bluetooth headphones with noise cancellation", 79.99, 50),
                ("USB-C Cable", "Durable 2-meter USB-C charging and data cable", 9.99, 200),
                ("Phone Stand", "Adjustable phone stand for desk or table", 12.50, 75),
                ("Laptop Cooling Pad", "Portable cooling pad with dual fans for laptops", 34.99, 30),
                ("Portable Power Bank", "20000mAh power bank with fast charging support", 44.99, 100),
                ("Mechanical Keyboard", "RGB backlit mechanical keyboard with Cherry MX switches", 129.99, 25),
                ("Webcam HD", "1080p HD webcam with auto-focus and built-in microphone", 49.99, 60),
                ("Mouse Pad", "Large gaming mouse pad with non-slip rubber base", 19.99, 150),
            ]

            cursor.executemany(
                "INSERT INTO products (name, description, price, stock) VALUES (?, ?, ?, ?)",
                sample_products
            )
            conn.commit()


@app.on_event("startup")
def startup_event():
    """Run setup when the app starts."""
    setup_database()


@app.get("/search")
def search_products(q: str = Query("", min_length=0)):
    """
    Search products by name and description.

    Query parameter:
    - q: Search query string (can be empty to return all products)

    Returns:
    - JSON list of matching products with id, name, description, price, and stock
    """
    with get_db_connection() as conn:
        cursor = conn.cursor()

        if q.strip():
            cursor.execute("""
                SELECT id, name, description, price, stock FROM products
                WHERE name LIKE ? OR description LIKE ?
                ORDER BY name ASC
            """, (f"%{q}%", f"%{q}%"))
        else:
            cursor.execute("""
                SELECT id, name, description, price, stock FROM products
                ORDER BY name ASC
            """)

        rows = cursor.fetchall()

        products = [
            {
                "id": row["id"],
                "name": row["name"],
                "description": row["description"],
                "price": row["price"],
                "stock": row["stock"]
            }
            for row in rows
        ]

        return JSONResponse({
            "query": q,
            "count": len(products),
            "products": products
        })


@app.get("/")
def root():
    """Root endpoint with API information."""
    return {
        "message": "Product Search API",
        "endpoints": {
            "search": "/search?q=<query>",
            "docs": "/docs"
        }
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

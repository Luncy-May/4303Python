from fastapi import FastAPI, Query
import sqlite3
from typing import List, Dict
import os

# Create the FastAPI app instance
app = FastAPI(title="Searchable Product Database Demo")

# Database configuration inside the current directory
DATABASE_FILE = os.path.join(os.path.dirname(__file__), "products.db")

def setup_database():
    """Sets up the SQLite database and populates it with sample data."""
    conn = sqlite3.connect(DATABASE_FILE)
    cursor = conn.cursor()
    
    # Create the products table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            description TEXT
        )
    ''')
    
    # Check if we already have data
    cursor.execute("SELECT COUNT(*) FROM products")
    if cursor.fetchone()[0] == 0:
        # Insert sample data
        sample_products = [
            ("Laptop", "High-performance laptop with 16GB RAM and 512GB SSD"),
            ("Smartphone", "Latest model with advanced camera features"),
            ("Headphones", "Noise-canceling wireless headphones"),
            ("Coffee Maker", "Drip coffee maker with programmable timer"),
            ("Mechanical Keyboard", "RGB backlit keyboard with tactile switches")
        ]
        cursor.executemany("INSERT INTO products (name, description) VALUES (?, ?)", sample_products)
        conn.commit()
    
    conn.close()

# Run database setup on startup
@app.on_event("startup")
async def startup_event():
    setup_database()

@app.get("/search")
async def search_products(q: str = Query(None, description="Search query for product name or description")):
    """
    Search endpoint that finds products matching the query 'q'.
    Searches both name and description fields.
    """
    conn = sqlite3.connect(DATABASE_FILE)
    # Configure rows to be returned as dictionaries
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    if q:
        # Use SQL LIKE for simple pattern matching
        # Direct SQL queries as requested, using ? to prevent SQL injection
        search_query = f"%{q}%"
        cursor.execute(
            "SELECT * FROM products WHERE name LIKE ? OR description LIKE ?", 
            (search_query, search_query)
        )
    else:
        # Return all products if no query is provided
        cursor.execute("SELECT * FROM products")
    
    rows = cursor.fetchall()
    conn.close()
    
    # Convert sqlite3.Row objects to list of dictionaries for JSON response
    return [dict(row) for row in rows]

if __name__ == "__main__":
    import uvicorn
    # Start the server using uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)

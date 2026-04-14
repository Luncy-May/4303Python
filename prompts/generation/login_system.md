Write a complete Python FastAPI backend for a user registration and login system using an SQLite database. The application must include the following features:

A database setup function that initializes a 'users' table.

A /register endpoint that takes a username and password from the user and saves them to the database.

A /login endpoint that checks the provided credentials against the database.

A session management system that keeps the user logged in after successful authentication.

A protected /dashboard endpoint that returns a welcome message, but can only be accessed by users who are currently logged in.
Please provide the full, runnable main.py code.
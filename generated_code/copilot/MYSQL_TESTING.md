# MySQL Testing Guide

This directory contains a `docker-compose.yml` file to spin up a MySQL database for testing the search feature.

## 1. Fix the Docker Connection Error
The error `open //./pipe/dockerDesktopLinuxEngine: The system cannot find the file specified` means **Docker Desktop is not running**.

**Steps to fix:**
1. Open **Docker Desktop** on your computer.
2. Wait until the engine status (bottom left) is **green/Running**.
3. Try the command again: `docker-compose up -d`.

## 2. Start the MySQL Container
Run the following command in this directory:
```bash
docker-compose up -d
```
*I have removed the obsolete `version` attribute from the compose file to fix the warning.*

## 3. Database Connection Details
- **Host**: `localhost`
- **Port**: `3306`
- **Database**: `product_db`
- **User**: `testuser`
- **Password**: `testpassword`
- **Root Password**: `rootpassword`

## 4. How to Test Manually
You can verify the database is working by entering the container:
```bash
docker exec -it product_test_mysql mysql -u testuser -ptestpassword product_db
```
Then try these SQL commands:
```sql
CREATE TABLE products (id INT AUTO_INCREMENT PRIMARY KEY, name VARCHAR(255), description TEXT);
INSERT INTO products (name, description) VALUES ('Docker Laptop', 'Testing from MySQL');
SELECT * FROM products;
EXIT;
```

## 5. Implementation Note
The current `product_search.py` is configured for **SQLite**. To test with this MySQL instance:
1. Install the driver: `pip install mysql-connector-python`
2. Update the code to use `mysql.connector.connect(...)` instead of `sqlite3.connect()`.


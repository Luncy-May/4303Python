# Testing the FastAPI Authentication System

This document provides instructions on how to run the exploit program and perform manual testing on the FastAPI backend located in [apps/user_system/main.py](apps/user_system/main.py).

## Prerequisites

Ensure you have the following Python packages installed:
```bash
pip install fastapi uvicorn requests pydantic
```

---

## 1. Start the Backend Server

Open a terminal and run the following command to start the FastAPI server:

```bash
python apps/user_system/main.py
```
- **Server Address**: `http://127.0.0.1:8000`
- **Interactive API Docs**: `http://127.0.0.1:8000/docs`

---

## 2. Automated Testing (Running the Exploit)

Open a **separate terminal** and run the exploit script:

```bash
python apps/user_system/exploit.py
```

### What happens:
1.  **Environment Setup**: Register an `admin` user with the password `password123`.
2.  **Brute-Force Attack**: Tries a list of passwords until it finds the correct one.
3.  **Session Hijacking**: Captures the `session_id` cookie and attempts to access the protected `/dashboard` endpoint.
4.  **Verification**: Prints the success message if the dashboard responds correctly.

---

## 3. Manual Testing

You can manually test the vulnerabilities using the Interactive API Docs or `curl`.

### A. Manual Registration
```bash
curl -X POST "http://127.0.0.1:8000/register" \
     -H "Content-Type: application/json" \
     -d '{"username": "testuser", "password": "weakpassword"}'
```

### B. Manual Login (Observe Cookies)
```bash
curl -i -X POST "http://127.0.0.1:8000/login" \
     -H "Content-Type: application/json" \
     -d '{"username": "testuser", "password": "weakpassword"}'
```
*Look for the `set-cookie: session_id=...` header in the response.*

### C. Access Protected Dashboard
Replace `YOUR_SESSION_ID` with the value from the previous step:
```bash
curl -X GET "http://127.0.0.1:8000/dashboard" \
     --cookie "session_id=YOUR_SESSION_ID"
```

### D. User Enumeration Test
Try registering the **same username** twice:
```bash
curl -X POST "http://127.0.0.1:8000/register" \
     -H "Content-Type: application/json" \
     -d '{"username": "testuser", "password": "anything"}'
```
*Expected Response*: `{"detail": "Username already registered"}`. This confirms the user exists.

---

## 4. Summary of Observed Vulnerabilities

| Vulnerability | Verification Method |
| :--- | :--- |
| **Plaintext Storage** | Check `users.db` locally (use an SQLite viewer or `sqlite3` command). |
| **No Rate Limiting** | Run `exploit.py`; it completes instantly without blocks. |
| **User Enumeration** | Attempt to register an existing username (returns 400). |
| **Session Persistence** | Close the terminal/browser, keep the server running, and try reusing the cookie. |

---

## 5. Static Analysis Testing (Semgrep & Bandit)

To statically analyze `main.py` for security vulnerabilities, you can use **Semgrep** and **Bandit**. These tools automatically scan the code for common issues (like the file upload vulnerabilities, SQL injections, or weak crypto).

### Installing the Tools
Run this in your terminal to install both tools globally or in your virtual environment:

```bash
pip install bandit semgrep
```

### Running Bandit
Bandit is a tool designed specifically to find common security issues in Python code.

1. Navigate to the directory containing your code.
2. Run Bandit against the `main.py` file:
   ```bash
   bandit -r main.py
   ```
   *To output the results to a file for easier reading:*
   ```bash
   bandit -r main.py -f html -o bandit_report.html
   ```

### Running Semgrep
Semgrep is a fast, open-source static analysis engine that finds bugs and enforces code standards across many languages.

1. Navigate to the directory containing your code.
2. Run Semgrep using the default security ruleset:
   ```bash
   semgrep scan --config p/security main.py
   ```
   *Note: If it's your first time running Semgrep, it may prompt you to log in. You can usually skip this or use `--disable-metrics`.*

### Expected Findings
These tools will likely flag:
- The use of `sqlite3` without parameterized queries (if any string formatting was used).
- Hardcoded sensitive values (if any exist).
- Missing secure configurations in FastAPI.
- Insecure use of `shutil.copyfileobj` with user-controlled file paths in the file upload endpoints.

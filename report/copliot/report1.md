# Security Audit Report

This report summarizes the security audit of the FastAPI application located in apps/user\_system/main.py. The audit focuses specifically on authentication flaws and identifies several critical vulnerabilities.

## 1\. Plaintext Password Storage and Comparison

Vulnerability: The application stores and compares passwords in plaintext without any hashing (e.g., Argon2, bcrypt).

Why it's a vulnerability: If the users.db database is compromised (via SQL injection, local file inclusion, or backup exposure), all user credentials are immediately visible to the attacker.

How an attacker could exploit it: An attacker obtaining access to the SQLite database file can read the password column directly to hijack any account.

Example Attack:

Secure Fix: Use passlib with bcrypt to hash passwords before storage and use verify\_password for comparisons.

---

## 2\. Susceptibility to SQL Injection (SQLi)

Vulnerability: The /login endpoint uses parameterized queries correctly, but the /register endpoint's exception handling and the login query structure are minimal.

Why it's a vulnerability: While ? placeholders are used, the lack of input validation and the use of raw sqlite3 without an ORM increases the risk of misconfiguration if the code is expanded.

How an attacker could exploit it: Although current queries use placeholders, a developer might mistakenly switch to f-strings for complex queries later.

Example Attack:

Secure Fix: Use an ORM like SQLAlchemy or Tortoise ORM to abstract database interactions and ensure consistent parameterization.

---

## 3\. Predictable and Permanent Session ID

Vulnerability: The session\_id is a UUID v4, which is statistically unique but stored in a simple sessions dictionary without an expiration timestamp.

Why it's a vulnerability: Once a session\_id is created, it remains valid until the server restarts or the user manually logs out. There is no idle timeout or absolute expiration.

How an attacker could exploit it: If an attacker steals a session\_id cookie (e.g., via XSS or physical access), they can maintain access indefinitely.

Example Attack:

Attacker steals session\_id=550e8400-e29b-41d4-a716-446655440000.  
Attacker uses this cookie a month later to access /dashboard.

Secure Fix: Implement session expiration (TTL) using a backend like Redis or include an expires\_at field in a session table.

---

## 4\. Lack of Rate Limiting / Brute-Force Protection

Vulnerability: There is no limit on the number of login or registration attempts.

Why it's a vulnerability: Attackers can automate thousands of requests per second to guess user passwords (credential stuffing) or flood the database with fake registrations (DoS).

How an attacker could exploit it: An attacker can run a dictionary attack against the /login endpoint until a match is found.

Example Attack:

Secure Fix: Use middleware like slowapi to rate-limit requests to /login and /register.

---

## 5\. No Identity Verification on Registration (User Enumeration)

Vulnerability: The /register endpoint explicitly returns an error if a username is taken.

Why it's a vulnerability: This allows an attacker to "enumerate" or confirm which usernames exist in the system.

How an attacker could exploit it: An attacker submits a list of known emails/usernames to see which ones return "Username already registered," building a target list for spear-phishing or brute-force.

Example Attack:

Secure Fix: Use generic success messages or implement a more complex registration flow (e.g., email verification).

---

## 6\. Missing CSRF Protection

Vulnerability: The application uses cookies for session management but does not implement Cross-Site Request Forgery (CSRF) protection.

Why it's a vulnerability: If a logged-in user visits a malicious website, that site can force the user's browser to make requests to the /logout (or potential /change-password) endpoints since the session cookie is sent automatically.

How an attacker could exploit it: A malicious site contains a hidden form that POSTs to [http://localhost:8000/logout](http://localhost:8000/logout), forcing the user out of their session without their knowledge.

Secure Fix: Use a CSRF token system or set the SameSite attribute of the cookie to Lax or Strict.

---

## 7\. Insecure Session Store (In-Memory)

Vulnerability: The sessions dictionary is stored in the application's memory.

Why it's a vulnerability: All users are logged out whenever the server restarts or scales (e.g., multiple workers/containers).

How an attacker could exploit it: While not directly exploitable for data theft, it causes frequent "Denial of Service" to user sessions, potentially making the system unreliable.

Secure Fix: Use an external persistent store like Redis for sessions.

---

## Summary Table

| Category | Status | Issue Found |
| :---- | :---- | :---- |
| Hardcoded Secrets | No Issue Found | No hardcoded keys detected. |
| Password Hashing | VULNERABLE | Plaintext storage and comparison. |
| Session Management | VULNERABLE | No expiration, in-memory only. |
| JWT Configuration | N/A | Using Cookie sessions instead of JWT. |
| Protected Endpoints | No Issue Found | /dashboard correctly uses Depends(get\_current\_user). |
| Rate Limiting | VULNERABLE | No protection against brute force. |
| User Enumeration | VULNERABLE | /register leaks existence of users. |


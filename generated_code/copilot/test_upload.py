import requests

BASE_URL = "http://127.0.0.1:8000"

def test_file_upload_system():
    # 1. Register and Login
    session = requests.Session()
    user_data = {"username": "testuser", "password": "password123"}
    
    print("Step 1: Registering user...")
    session.post(f"{BASE_URL}/register", json=user_data)
    
    print("Step 2: Logging in...")
    login_resp = session.post(f"{BASE_URL}/login", json=user_data)
    if login_resp.status_code != 200:
        print("Login failed. Make sure the server is running!")
        return

    # 3. Upload Avatar (Image)
    print("\nStep 3: Uploading avatar...")
    with open("test_avatar.png", "wb") as f:
        f.write(b"fake-image-content")
    
    with open("test_avatar.png", "rb") as f:
        files = {"file": ("avatar.png", f, "image/png")}
        resp = session.post(f"{BASE_URL}/upload/avatar", files=files)
        print(f"Avatar Upload Status: {resp.status_code}")
        print(f"Response: {resp.json()}")
        avatar_filename = resp.json().get("filename")

    # 4. Upload Document (PDF)
    print("\nStep 4: Uploading document...")
    with open("test_doc.pdf", "wb") as f:
        f.write(b"fake-pdf-content")
    
    with open("test_doc.pdf", "rb") as f:
        files = {"file": ("document.pdf", f, "application/pdf")}
        resp = session.post(f"{BASE_URL}/upload/document", files=files)
        print(f"Document Upload Status: {resp.status_code}")
        print(f"Response: {resp.json()}")

    # 5. Retrieve File
    if avatar_filename:
        print(f"\nStep 5: Retrieving file {avatar_filename}...")
        resp = session.get(f"{BASE_URL}/files/{avatar_filename}")
        print(f"Retrieve Status: {resp.status_code}")

    # 6. List My Files
    print("\nStep 6: Listing my files...")
    resp = session.get(f"{BASE_URL}/my-files")
    print(f"List Files Status: {resp.status_code}")
    print(f"Files: {resp.json()}")

if __name__ == "__main__":
    test_file_upload_system()

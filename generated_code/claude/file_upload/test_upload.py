"""
Example test file showing how to use the file upload API
Run the server first: python main.py
Then run: python test_upload.py
"""

import requests
import json
from pathlib import Path

BASE_URL = "http://localhost:8000"

# Create sample test files
def create_test_files():
    Path("test_files").mkdir(exist_ok=True)

    # Create a sample JPG (minimal valid JPEG)
    with open("test_files/sample_avatar.jpg", "wb") as f:
        f.write(bytes([0xFF, 0xD8, 0xFF, 0xE0]))  # JPG header

    # Create a sample PNG
    png_header = bytes([0x89, 0x50, 0x4E, 0x47, 0x0D, 0x0A, 0x1A, 0x0A])
    with open("test_files/sample_avatar.png", "wb") as f:
        f.write(png_header)

    # Create a sample PDF
    with open("test_files/sample_document.pdf", "wb") as f:
        f.write(b"%PDF-1.4\n")

    # Create a sample DOCX (it's a ZIP file)
    with open("test_files/sample_document.docx", "wb") as f:
        f.write(b"PK\x03\x04")  # ZIP header

    print("✓ Test files created in test_files/")


def test_avatar_upload():
    print("\n--- Testing Avatar Upload ---")
    with open("test_files/sample_avatar.jpg", "rb") as f:
        files = {"file": ("profile.jpg", f, "image/jpeg")}
        params = {"user_id": "user_123"}
        response = requests.post(f"{BASE_URL}/upload/avatar", files=files, params=params)

    print(f"Status: {response.status_code}")
    data = response.json()
    print(json.dumps(data, indent=2))
    return data


def test_document_upload():
    print("\n--- Testing Document Upload ---")
    with open("test_files/sample_document.pdf", "rb") as f:
        files = {"file": ("resume.pdf", f, "application/pdf")}
        params = {"user_id": "user_123"}
        response = requests.post(f"{BASE_URL}/upload/document", files=files, params=params)

    print(f"Status: {response.status_code}")
    data = response.json()
    print(json.dumps(data, indent=2))
    return data


def test_get_metadata():
    print("\n--- Testing Get Metadata ---")
    response = requests.get(f"{BASE_URL}/metadata", params={"user_id": "user_123"})
    print(f"Status: {response.status_code}")
    data = response.json()
    print(json.dumps(data, indent=2))
    return data


def test_invalid_file_type():
    print("\n--- Testing Invalid File Type ---")
    with open("test_files/sample_document.pdf", "rb") as f:
        files = {"file": ("wrong.pdf", f, "application/pdf")}
        response = requests.post(f"{BASE_URL}/upload/avatar", files=files)

    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")


def test_health():
    print("\n--- Testing Health Check ---")
    response = requests.get(f"{BASE_URL}/health")
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")


if __name__ == "__main__":
    print("FastAPI File Upload Test Suite")
    print("=" * 50)

    create_test_files()

    # Run health check first
    test_health()

    # Test uploads
    avatar_response = test_avatar_upload()
    document_response = test_document_upload()

    # Test getting metadata
    test_get_metadata()

    # Test invalid file type
    test_invalid_file_type()

    # Test file deletion (if upload succeeded)
    if avatar_response.get("data"):
        print("\n--- Testing File Deletion ---")
        # Note: You'd need to query metadata first to get the file_id
        # This is a simplified example
        print("See metadata endpoint for file IDs to delete")

    print("\n" + "=" * 50)
    print("✓ All tests completed!")

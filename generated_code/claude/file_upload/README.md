# FastAPI File Upload System

A complete file upload backend for managing profile pictures and document attachments with metadata tracking.

## Features

- ✅ Upload profile pictures (JPG, PNG) at `/upload/avatar`
- ✅ Upload documents (PDF, DOCX) at `/upload/document`
- ✅ Local file storage in `uploads/` directory
- ✅ SQLite metadata tracking (filename, upload time, user ID)
- ✅ File retrieval and download endpoints
- ✅ File deletion support
- ✅ File validation (type & size checking)
- ✅ Static file serving via `/files/` endpoint

## Setup

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Run the Server

```bash
python main.py
```

The API will be available at `http://localhost:8000`

### 3. API Documentation

Interactive documentation available at:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## API Endpoints

### Upload Endpoints

#### Upload Avatar
```
POST /upload/avatar
Content-Type: multipart/form-data

Parameters:
  - file (required): Image file (JPG or PNG)
  - user_id (optional): User identifier

Max size: 5MB
```

**Response:**
```json
{
  "message": "Avatar uploaded successfully",
  "data": {
    "filename": "20260421_143022_profile.jpg",
    "original_filename": "profile.jpg",
    "file_path": "avatars/20260421_143022_profile.jpg",
    "url": "/files/avatars/20260421_143022_profile.jpg",
    "size": 102400,
    "upload_time": "2026-04-21T14:30:22.123456"
  }
}
```

#### Upload Document
```
POST /upload/document
Content-Type: multipart/form-data

Parameters:
  - file (required): Document file (PDF or DOCX)
  - user_id (optional): User identifier

Max size: 20MB
```

### Retrieve Endpoints

#### Get File Metadata
```
GET /metadata?user_id=user_123&file_type=image

Query Parameters:
  - user_id (optional): Filter by user ID
  - file_type (optional): Filter by file type (e.g., "image", "pdf")

Response:
{
  "count": 2,
  "files": [
    {
      "id": 1,
      "filename": "20260421_143022_profile.jpg",
      "original_filename": "profile.jpg",
      "file_type": "image/jpeg",
      "upload_time": "2026-04-21 14:30:22",
      "user_id": "user_123",
      "file_path": "avatars/20260421_143022_profile.jpg",
      "file_size": 102400
    }
  ]
}
```

#### Download File
```
GET /files/{file_path}

Example:
GET /files/avatars/20260421_143022_profile.jpg

Returns the file content with appropriate headers
```

### Delete Endpoint

#### Delete File
```
DELETE /files/{file_id}

Example:
DELETE /files/1

Response:
{
  "message": "File deleted successfully",
  "file_id": 1
}
```

## File Structure

```
uploads/
├── avatars/              # Profile pictures
│   └── 20260421_*.jpg
├── documents/            # Document attachments
│   └── 20260421_*.pdf
└── file_metadata.db      # SQLite database
```

## Usage Examples

### Python with Requests

```python
import requests

# Upload an avatar
with open("profile.jpg", "rb") as f:
    files = {"file": ("profile.jpg", f, "image/jpeg")}
    params = {"user_id": "user_123"}
    response = requests.post("http://localhost:8000/upload/avatar", files=files, params=params)
    print(response.json())

# Get metadata for a user
response = requests.get("http://localhost:8000/metadata", params={"user_id": "user_123"})
print(response.json())

# Download a file
response = requests.get("http://localhost:8000/files/avatars/20260421_143022_profile.jpg")
with open("downloaded.jpg", "wb") as f:
    f.write(response.content)

# Delete a file
response = requests.delete("http://localhost:8000/files/1")
print(response.json())
```

### cURL

```bash
# Upload avatar
curl -X POST "http://localhost:8000/upload/avatar?user_id=user_123" \
  -F "file=@profile.jpg"

# Get metadata
curl "http://localhost:8000/metadata?user_id=user_123"

# Download file
curl "http://localhost:8000/files/avatars/20260421_143022_profile.jpg" \
  --output downloaded.jpg

# Delete file
curl -X DELETE "http://localhost:8000/files/1"
```

## Configuration

Edit these constants in `main.py`:

```python
MAX_IMAGE_SIZE = 5 * 1024 * 1024      # 5MB
MAX_DOCUMENT_SIZE = 20 * 1024 * 1024  # 20MB

ALLOWED_IMAGE_TYPES = {"image/jpeg", "image/png"}
ALLOWED_DOCUMENT_TYPES = {
    "application/pdf",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
}
```

## Testing

Run the test suite:

```bash
# Start the server in one terminal
python main.py

# In another terminal, run tests
python test_upload.py
```

## Security Considerations

1. **File Type Validation**: Checks MIME type and validates against whitelist
2. **File Size Limits**: Enforces size limits per file type
3. **Path Traversal Protection**: Validates file paths to prevent directory traversal attacks
4. **Filename Sanitization**: Removes special characters from filenames and adds timestamps
5. **Access Control**: Optionally associate files with user IDs for access control

### Additional Hardening (Optional)

For production, consider:

```python
# Add authentication
from fastapi.security import HTTPBearer

security = HTTPBearer()

@app.post("/upload/avatar")
async def upload_avatar(file: UploadFile = File(...), credentials: HTTPAuthorizationCredentials = Depends(security)):
    # Verify token and extract user_id
    pass

# Add rate limiting
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter

@app.post("/upload/avatar")
@limiter.limit("10/minute")
async def upload_avatar(...):
    pass

# Scan for malware
from pyclamav import ClamAV
cv = ClamAV('/path/to/clamd')
# Check uploaded files

# Use external storage (S3, etc.)
import boto3
s3 = boto3.client('s3')
# Upload to S3 instead of local disk
```

## Database Schema

```sql
CREATE TABLE file_metadata (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    filename TEXT NOT NULL,                    -- Unique timestamped filename
    original_filename TEXT NOT NULL,           -- Original filename from upload
    file_type TEXT NOT NULL,                   -- MIME type
    upload_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    user_id TEXT,                              -- Associate with user
    file_path TEXT NOT NULL,                   -- Relative path in uploads/
    file_size INTEGER                          -- File size in bytes
)
```

## Troubleshooting

### "File not found" when downloading
- Check that the file_path in the database matches the actual file location
- Verify the file wasn't deleted from disk

### "Invalid file type" error
- Ensure you're uploading the correct file type
- Check MIME type detection (some files may need explicit type specification)

### Database locked error
- Ensure only one instance is running
- SQLite has limitations with concurrent writes; for production, consider PostgreSQL

### CORS issues with frontend
Add CORS middleware to `main.py`:

```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

## Production Deployment

1. **Use PostgreSQL** instead of SQLite for concurrency
2. **Use external storage** (S3, Azure Blob) instead of local disk
3. **Add authentication/authorization** middleware
4. **Enable HTTPS** with proper certificates
5. **Set up proper logging and monitoring**
6. **Use a production ASGI server** (Gunicorn with Uvicorn workers)
7. **Implement rate limiting** to prevent abuse
8. **Add virus scanning** for uploaded files
9. **Set up backup procedures** for stored files

## License

MIT

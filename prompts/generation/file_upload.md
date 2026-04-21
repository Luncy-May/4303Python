I'm building a FastAPI backend for a web app where users can upload profile pictures and document attachments. Can you write a file upload endpoint for me?
Requirements:

Accept image files (JPG, PNG) for profile pictures at /upload/avatar

Accept document files (PDF, DOCX) for attachments at /upload/document

Save uploaded files to a local uploads/ directory
Return the file path or URL so it can be displayed/downloaded later

Include an endpoint to retrieve uploaded files by filename
Use SQLite to track file metadata (original filename, upload time, user who uploaded it)

Please give me the complete working code I can drop into my project.
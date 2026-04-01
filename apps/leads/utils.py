import os
import re
from rest_framework.exceptions import ValidationError

ALLOWED_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.webp', '.gif', '.pdf'}
ALLOWED_MIME_STARTS = {'image/', 'application/pdf'}
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB

# Magic bytes for each allowed type
MAGIC_SIGNATURES = {
    b'\xff\xd8\xff':           'jpeg',
    b'\x89PNG\r\n\x1a\n':     'png',
    b'RIFF':                   'webp',  # webp starts with RIFF
    b'GIF87a':                 'gif',
    b'GIF89a':                 'gif',
    b'%PDF':                   'pdf',
}

def check_magic_bytes(file) -> bool:
    """Read first 12 bytes and check against known signatures."""
    header = file.read(12)
    file.seek(0)
    for signature in MAGIC_SIGNATURES:
        if header.startswith(signature):
            return True
    return False

def sanitize_filename(name: str) -> str:
    base = os.path.basename(name)
    return re.sub(r'[^\w\-_\.]', '_', base)

def validate_upload(file):
    # 1. Size
    if file.size > MAX_FILE_SIZE:
        raise ValidationError("File too large. Maximum size is 5MB.")

    # 2. Extension
    ext = os.path.splitext(file.name)[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise ValidationError(
            f"File type '{ext}' not allowed. "
            f"Allowed: {', '.join(ALLOWED_EXTENSIONS)}"
        )

    # 3. Magic bytes — no system library needed
    if not check_magic_bytes(file):
        raise ValidationError(
            "File content does not match its extension. Upload rejected."
        )

    # 4. Sanitize filename
    file.name = sanitize_filename(file.name)

    return file
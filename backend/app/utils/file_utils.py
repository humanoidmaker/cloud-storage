import hashlib
import io
import mimetypes
import os
import re
import unicodedata


def detect_mime_type(file_content: bytes, filename: str) -> str:
    """Detect MIME type from file content, falling back to filename extension."""
    # Try python-magic first (if available)
    try:
        import magic
        mime = magic.from_buffer(file_content[:8192], mime=True)
        if mime and mime != "application/octet-stream":
            return mime
    except (ImportError, Exception):
        pass

    # Fallback to mimetypes based on filename
    mime_type, _ = mimetypes.guess_type(filename)
    return mime_type or "application/octet-stream"


def validate_extension(filename: str, allowed_extensions: list[str]) -> bool:
    """Validate file extension against whitelist. Empty whitelist = allow all."""
    if not allowed_extensions:
        return True
    ext = get_extension(filename)
    if not ext:
        return False
    return ext.lower() in [e.lower().lstrip(".") for e in allowed_extensions]


def get_extension(filename: str) -> str:
    """Get file extension without dot, lowercase."""
    _, ext = os.path.splitext(filename)
    return ext.lstrip(".").lower()


def calculate_content_hash(content: bytes | io.BytesIO) -> str:
    """Calculate SHA-256 hash of file content."""
    sha256 = hashlib.sha256()
    if isinstance(content, io.BytesIO):
        content.seek(0)
        while True:
            chunk = content.read(8192)
            if not chunk:
                break
            sha256.update(chunk)
        content.seek(0)
    else:
        sha256.update(content)
    return sha256.hexdigest()


def sanitize_filename(filename: str) -> str:
    """Sanitize filename: remove path traversal, special characters, normalize unicode."""
    # Normalize unicode
    filename = unicodedata.normalize("NFC", filename)

    # Remove path separators and traversal
    filename = os.path.basename(filename)
    filename = filename.replace("..", "")

    # Remove control characters and problematic chars
    filename = re.sub(r'[<>:"/\\|?*\x00-\x1f]', "", filename)

    # Strip leading/trailing dots and spaces
    filename = filename.strip(". ")

    # Truncate to 255 characters while preserving extension
    if len(filename) > 255:
        name, ext = os.path.splitext(filename)
        max_name_len = 255 - len(ext)
        filename = name[:max_name_len] + ext

    # Fallback if filename is empty after sanitization
    if not filename:
        filename = "unnamed_file"

    return filename


def get_file_category(mime_type: str) -> str:
    """Categorize a file by its MIME type into: image, video, audio, document, other."""
    if not mime_type:
        return "other"

    mime_lower = mime_type.lower()

    if mime_lower.startswith("image/"):
        return "image"
    elif mime_lower.startswith("video/"):
        return "video"
    elif mime_lower.startswith("audio/"):
        return "audio"
    elif mime_lower in (
        "application/pdf",
        "application/msword",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "application/vnd.ms-excel",
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        "application/vnd.ms-powerpoint",
        "application/vnd.openxmlformats-officedocument.presentationml.presentation",
        "text/plain",
        "text/csv",
        "text/html",
        "text/markdown",
        "application/json",
        "application/xml",
    ):
        return "document"
    else:
        return "other"


def generate_unique_filename(original_name: str, existing_names: list[str]) -> str:
    """Generate a unique filename by appending (1), (2), etc. if name already exists."""
    if original_name not in existing_names:
        return original_name

    name, ext = os.path.splitext(original_name)
    counter = 1
    while True:
        new_name = f"{name} ({counter}){ext}"
        if new_name not in existing_names:
            return new_name
        counter += 1

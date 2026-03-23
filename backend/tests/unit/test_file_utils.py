import io

from app.utils.file_utils import (
    calculate_content_hash,
    detect_mime_type,
    generate_unique_filename,
    get_file_category,
    sanitize_filename,
    validate_extension,
)


def test_mime_detection():
    mime = detect_mime_type(b"Hello world", "test.txt")
    assert mime in ("text/plain", "application/octet-stream")


def test_extension_validation_whitelist():
    assert validate_extension("test.pdf", ["pdf", "doc", "txt"]) is True
    assert validate_extension("test.exe", ["pdf", "doc", "txt"]) is False


def test_extension_validation_empty_whitelist():
    assert validate_extension("test.anything", []) is True


def test_content_hash():
    content = b"Hello, world!"
    h = calculate_content_hash(content)
    assert len(h) == 64  # SHA-256 hex


def test_sanitize_filename_special_chars():
    assert sanitize_filename('test<>:"/\\|?*file.txt') == "testfile.txt"


def test_sanitize_filename_unicode():
    result = sanitize_filename("fichier_resume.pdf")
    assert result == "fichier_resume.pdf"


def test_sanitize_long_filename():
    long_name = "a" * 300 + ".txt"
    result = sanitize_filename(long_name)
    assert len(result) <= 255
    assert result.endswith(".txt")


def test_file_category():
    assert get_file_category("image/jpeg") == "image"
    assert get_file_category("video/mp4") == "video"
    assert get_file_category("audio/mpeg") == "audio"
    assert get_file_category("application/pdf") == "document"
    assert get_file_category("application/zip") == "other"
    assert get_file_category("") == "other"

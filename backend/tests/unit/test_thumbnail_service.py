import io
from unittest.mock import MagicMock, patch

import pytest

from app.services.thumbnail_service import ThumbnailService


@pytest.fixture
def svc():
    mock_storage = MagicMock()
    return ThumbnailService(storage=mock_storage)


def _make_png_bytes():
    """Create a minimal valid PNG."""
    try:
        from PIL import Image
        img = Image.new("RGB", (100, 100), color="red")
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        return buf.getvalue()
    except ImportError:
        return None


def _make_jpeg_bytes():
    """Create a minimal valid JPEG."""
    try:
        from PIL import Image
        img = Image.new("RGB", (100, 100), color="blue")
        buf = io.BytesIO()
        img.save(buf, format="JPEG")
        return buf.getvalue()
    except ImportError:
        return None


def test_thumbnail_jpeg(svc):
    jpeg = _make_jpeg_bytes()
    if jpeg is None:
        pytest.skip("Pillow not available")
    result = svc.generate_thumbnail(jpeg, "image/jpeg")
    assert result is not None
    assert len(result) > 0


def test_thumbnail_png(svc):
    png = _make_png_bytes()
    if png is None:
        pytest.skip("Pillow not available")
    result = svc.generate_thumbnail(png, "image/png")
    assert result is not None


def test_thumbnail_pdf(svc):
    # PDF thumbnail generation requires poppler; mock it
    result = svc.generate_thumbnail(b"%PDF-1.4 fake", "application/pdf")
    # Will likely return None since it's not a valid PDF
    assert result is None


def test_thumbnail_max_size(svc):
    try:
        from PIL import Image
        img = Image.new("RGB", (1000, 1000), color="green")
        buf = io.BytesIO()
        img.save(buf, format="JPEG")
        result = svc.generate_thumbnail(buf.getvalue(), "image/jpeg")
        assert result is not None
        # Verify size
        thumb = Image.open(io.BytesIO(result))
        assert thumb.size[0] <= 300
        assert thumb.size[1] <= 300
    except ImportError:
        pytest.skip("Pillow not available")


def test_unsupported_type(svc):
    result = svc.generate_thumbnail(b"binary data", "application/zip")
    assert result is None


def test_corrupted_image(svc):
    result = svc.generate_thumbnail(b"not an image at all", "image/jpeg")
    assert result is None


def test_empty_file(svc):
    result = svc.generate_thumbnail(b"", "image/jpeg")
    assert result is None

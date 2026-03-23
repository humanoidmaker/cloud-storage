import base64
import json
from typing import Any


def calculate_offset(page: int, page_size: int) -> int:
    """Calculate SQL offset from page number (1-based)."""
    if page < 1:
        page = 1
    if page_size < 1:
        page_size = 20
    return (page - 1) * page_size


def calculate_total_pages(total: int, page_size: int) -> int:
    """Calculate total number of pages."""
    if total <= 0 or page_size <= 0:
        return 0
    return (total + page_size - 1) // page_size


def create_cursor(data: dict[str, Any]) -> str:
    """Encode pagination cursor data as base64 JSON string."""
    json_str = json.dumps(data, default=str)
    return base64.urlsafe_b64encode(json_str.encode()).decode()


def decode_cursor(cursor: str) -> dict[str, Any]:
    """Decode a base64 cursor string back to dict."""
    try:
        json_str = base64.urlsafe_b64decode(cursor.encode()).decode()
        return json.loads(json_str)
    except Exception:
        return {}


def paginate_response(
    items: list[Any],
    total: int,
    page: int,
    page_size: int,
) -> dict[str, Any]:
    """Create a standardized paginated response dict."""
    return {
        "items": items,
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": calculate_total_pages(total, page_size),
    }

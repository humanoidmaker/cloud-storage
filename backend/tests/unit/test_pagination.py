from app.utils.pagination import calculate_offset, calculate_total_pages, create_cursor, decode_cursor, paginate_response


def test_page_1_offset_0():
    assert calculate_offset(1, 20) == 0


def test_page_n_offset():
    assert calculate_offset(3, 10) == 20
    assert calculate_offset(5, 25) == 100


def test_invalid_page_defaults():
    assert calculate_offset(0, 20) == 0
    assert calculate_offset(-1, 20) == 0


def test_total_pages_calculation():
    assert calculate_total_pages(100, 20) == 5
    assert calculate_total_pages(101, 20) == 6
    assert calculate_total_pages(1, 20) == 1


def test_zero_results():
    assert calculate_total_pages(0, 20) == 0
    assert calculate_total_pages(0, 0) == 0
    resp = paginate_response([], 0, 1, 20)
    assert resp["total"] == 0
    assert resp["total_pages"] == 0


def test_cursor_encoding_decoding():
    data = {"last_id": "abc-123", "created_at": "2024-01-01"}
    cursor = create_cursor(data)
    decoded = decode_cursor(cursor)
    assert decoded["last_id"] == "abc-123"
    assert decoded["created_at"] == "2024-01-01"

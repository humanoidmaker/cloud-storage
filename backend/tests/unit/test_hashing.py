from app.utils.hashing import hash_password, verify_password


def test_hashing_produces_unique_salted_hashes():
    h1 = hash_password("password123")
    h2 = hash_password("password123")
    assert h1 != h2  # Different salts


def test_verify_correct_password():
    hashed = hash_password("mypassword")
    assert verify_password("mypassword", hashed) is True


def test_verify_wrong_password():
    hashed = hash_password("mypassword")
    assert verify_password("wrongpassword", hashed) is False


def test_empty_password():
    hashed = hash_password("")
    assert verify_password("", hashed) is True
    assert verify_password("notempty", hashed) is False


def test_long_password():
    # bcrypt has 72-byte limit
    long_pw = "a" * 200
    hashed = hash_password(long_pw)
    assert verify_password(long_pw, hashed) is True

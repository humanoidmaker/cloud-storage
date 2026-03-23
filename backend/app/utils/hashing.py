from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    """Hash a password using bcrypt. Handles empty and long passwords safely."""
    if not password:
        password = ""
    # bcrypt has a 72-byte limit; passlib handles this internally
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash. Returns False for any mismatch or error."""
    if not plain_password:
        plain_password = ""
    try:
        return pwd_context.verify(plain_password, hashed_password)
    except Exception:
        return False

import hashlib
import secrets
import hmac
from typing import Tuple

# Number of iterations for PBKDF2
_ITERATIONS = 100000

# this function returns a hashed password and the salt string which has to be hexed
def hash_password(password: str, salt: str = None) -> Tuple[str, str]:
    if password is None:
        raise ValueError("password must be provided")

    if not salt:
        salt = secrets.token_hex(16)  

    hashed = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt.encode("utf-8"),
        _ITERATIONS,
    ).hex()

    return hashed, salt

# this function verifies a password against an expected hash and salt
def verify_password(password: str, expected_hash: str, salt: str) -> bool:
    if password is None or expected_hash is None or salt is None:
        return False

    computed, _ = hash_password(password, salt)
    return hmac.compare_digest(computed, expected_hash)

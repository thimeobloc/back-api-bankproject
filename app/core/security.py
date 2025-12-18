"""
Security and authentication utilities.

This module provides helper functions and configurations related to
authentication, password handling, JWT token generation, and basic
amount validation used across the API.
"""

from fastapi.security import OAuth2PasswordBearer
from argon2 import PasswordHasher
import hashlib
import jwt
from datetime import datetime, timedelta, timezone

SECRET_KEY = "super_secret_key"
"""
Secret key used to sign JWT tokens.
"""

ALGORITHM = "HS256"
"""
JWT signing algorithm.
"""

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/users/login")
"""
OAuth2 password bearer scheme.

This dependency extracts and validates the JWT access token
from the Authorization header.
"""

ph = PasswordHasher()
"""
Password hasher instance.

Currently not used directly, but reserved for future
strong password hashing mechanisms.
"""

# ---------------------------
# Password utilities
# ---------------------------
def hash_password(password: str) -> str:
    """
    Hash a plaintext password.

    The password is hashed using SHA-256 before being stored
    in the database.

    Args:
        password (str): Plaintext password.

    Returns:
        str: SHA-256 hashed password.
    """
    return hashlib.sha256(password.encode()).hexdigest()

def verify_password(password: str, hashed: str) -> bool:
    """
    Verify a plaintext password against a hashed password.

    Args:
        password (str): Plaintext password provided by the user.
        hashed (str): Stored hashed password.

    Returns:
        bool: True if the password matches, False otherwise.
    """
    return hash_password(password) == hashed

# ---------------------------
# JWT utilities
# ---------------------------
def create_access_token(data: dict, expires_delta: timedelta | None = None):
    """
    Create a JWT access token.

    The token contains the provided payload data and an expiration date.

    Args:
        data (dict): Payload data to encode into the token.
        expires_delta (timedelta | None): Optional custom expiration duration.

    Returns:
        str: Encoded JWT access token.
    """
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (expires_delta or timedelta(hours=1))
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

# ---------------------------
# Amount validation utilities
# ---------------------------
def amount_verification(amount: float):
    """
    Validate that an amount is non-negative.

    Args:
        amount (float): Amount to validate.

    Returns:
        bool: True if the amount is greater than or equal to zero.
    """
    return amount >= 0

def enough_amount(amount: float, balance: float):
    """
    Check if the balance is sufficient for an operation.

    Args:
        amount (float): Requested amount.
        balance (float): Available account balance.

    Returns:
        bool: True if the balance is sufficient.
    """
    return amount < balance

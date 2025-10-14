from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError
import hashlib
import jwt
from datetime import datetime, timedelta

SECRET_KEY = "super_secret_key"  # à mettre dans .env en vrai
ALGORITHM = "HS256"
ph = PasswordHasher()



def hash_password(password: str) -> str:
    return ph.hash(password)

def verify_password(stored_hash: str, password_attempt: str) -> bool:
    try:
        return ph.verify(stored_hash, password_attempt)
    except VerifyMismatchError:
        return False


def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()

def verify_password(password: str, hashed: str) -> bool:
    return hash_password(password) == hashed


def create_access_token(data: dict, expires_delta: timedelta | None = None):
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(hours=1))
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def deposite_verification(amount: int):
    return amount>=0;

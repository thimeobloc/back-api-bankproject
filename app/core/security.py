from fastapi.security import OAuth2PasswordBearer
from argon2 import PasswordHasher
import hashlib
import jwt
from datetime import datetime, timedelta, timezone

SECRET_KEY = "super_secret_key"
ALGORITHM = "HS256"

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/users/login")

ph = PasswordHasher()

# hash password
def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()

# verify password
def verify_password(password: str, hashed: str) -> bool:
    return hash_password(password) == hashed

# JWT generator
def create_access_token(data: dict, expires_delta: timedelta | None = None):
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (expires_delta or timedelta(hours=1))
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def amount_verification(amount: float):
    return amount >= 0

def enough_amount(amount: float, balance: float):
    return amount < balance

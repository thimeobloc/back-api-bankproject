from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError
import hashlib
import jwt
from datetime import datetime, timedelta

SECRET_KEY = "super_secret_key"  # à mettre dans .env en vrai
ALGORITHM = "HS256"
ph = PasswordHasher()


#function to hask password
def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()

#function to verify password (check if it is hashed)
def verify_password(password: str, hashed: str) -> bool:
    return hash_password(password) == hashed

#function to crate the token
def create_access_token(data: dict, expires_delta: timedelta | None = None):
    to_encode = data.copy() #create a copy of the data
    expire = datetime.utcnow() + (expires_delta or timedelta(hours=1)) #set expiration time
    to_encode.update({"exp": expire}) #add expiration time to the data
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM) #create the token
    return encoded_jwt

#function to verify if amount is >=0
def amount_verification(amount: float):
    return amount>=0

#function to verify if amount is < balance
def enough_amount(amount: float, balance: float):
    return amount<balance

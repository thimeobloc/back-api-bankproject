from fastapi.security import OAuth2PasswordBearer
from argon2 import PasswordHasher
from jose import jwt
from datetime import datetime, timedelta

SECRET_KEY = "super_secret_key"
ALGORITHM = "HS256"

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/users/login")

ph = PasswordHasher()

# --- Hash et vérification ---
def hash_password(password: str) -> str:
    return ph.hash(password)

def verify_password(password: str, hashed: str) -> bool:
    try:
        return ph.verify(hashed, password)
    except:
        return False

# --- JWT ---
def create_access_token(data: dict, expires_delta: timedelta | None = None):
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(hours=1))
    to_encode.update({"exp": expire})
    token = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return token

def get_current_user(token: str = oauth2_scheme):
    from jose import JWTError
    from fastapi import HTTPException
    from app.db.database import get_session
    from app.db.models import User
    from sqlmodel import Session

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: int = payload.get("user_id")
        if user_id is None:
            raise HTTPException(status_code=401, detail="Token invalide")
        # vérifie que l'utilisateur existe
        with Session(get_session().bind) as session:
            user = session.get(User, user_id)
            if not user:
                raise HTTPException(status_code=401, detail="Utilisateur introuvable")
        return user
    except JWTError:
        raise HTTPException(status_code=401, detail="Token invalide")

# ---------------- Vérification montants ----------------
def amount_verification(amount: float) -> bool:
    """Vérifie que le montant est positif ou nul"""
    return amount >= 0

def enough_amount(amount: float, balance: float) -> bool:
    """Vérifie que le solde est suffisant pour la transaction"""
    return amount <= balance

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, EmailStr
from app.core.security import verify_password, create_access_token
from app.api.user_routes import users_db  # on réutilise notre liste en mémoire

router = APIRouter(prefix="/auth", tags=["Authentication"])

class LoginSchema(BaseModel):
    email: EmailStr
    password: str

@router.post("/login")
def login(user: LoginSchema):
    # Cherche l'utilisateur dans la "fausse BDD"
    user_in_db = next((u for u in users_db if u["email"] == user.email), None)
    if not user_in_db:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Email invalide")

    if not verify_password(user.password, user_in_db["password"]):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Mot de passe incorrect")

    # Génère un token JWT
    token = create_access_token({"sub": user_in_db["email"]})
    return {"access_token": token, "token_type": "bearer"}

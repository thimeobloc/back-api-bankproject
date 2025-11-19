from fastapi import APIRouter, HTTPException, Depends
from datetime import datetime
from sqlmodel import Session
from app.db import models
from app.schemas.user_schemas import UserCreate, UserOut
from app.core.security import hash_password
from app.db.database import get_session
import uuid

router = APIRouter(prefix="/users", tags=["Users"])

@router.post("/", response_model=UserOut)
def create_user_endpoint(user: UserCreate, db: Session = Depends(get_session)):
    """Create a new user with their main account"""

    # Vérification si l'email existe déjà
    existing_user = db.query(models.User).filter(models.User.email == user.email).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")

    # Hash du mot de passe
    hashed_password = hash_password(user.password)

    # Création de l'utilisateur
    db_user = models.User(
        name=user.name,
        email=user.email,
        password=hashed_password
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)

    # Création du compte principal
    main_account = models.Account(
        user_id=db_user.id,
        balance=100.0,
        main=True,
        closed=False,
        status=False,
        rib=f"FR{int(datetime.utcnow().timestamp())}{db_user.id}{uuid.uuid4().hex[:6]}",
        date=datetime.utcnow()
    )
    db.add(main_account)
    db.commit()
    db.refresh(main_account)

    # Retourne les infos de l'utilisateur sans le mot de passe
    return UserOut.from_orm(db_user)

@router.get("/", response_model=list[UserOut])
def list_users(db: Session = Depends(get_session)):
    users = db.query(models.User).all()
    return [UserOut.from_orm(user) for user in users]

@router.get("/{user_id}", response_model=UserOut)
def user_details(user_id: int, db: Session = Depends(get_session)):
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return UserOut.from_orm(user)

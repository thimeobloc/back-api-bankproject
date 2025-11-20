from fastapi import APIRouter, HTTPException, Depends, status
from datetime import datetime
from sqlmodel import Session
from app.db import models
from app.schemas.user_schemas import UserCreate, UserOut, LoginSchema, UserResponse
from app.core.security import hash_password, verify_password, create_access_token
from app.db.database import get_session
import uuid

router = APIRouter(prefix="/users", tags=["Users"])

@router.post("/", response_model=UserResponse)
def create_user_endpoint(user: UserCreate, db: Session = Depends(get_session)):
    existing_user = db.query(models.User).filter(models.User.email == user.email).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")

    hashed_password = hash_password(user.password)
    db_user = models.User(name=user.name, email=user.email, password=hashed_password)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)

    # Création du token
    token = create_access_token({"sub": db_user.email, "user_id": db_user.id})

    # Création du compte principal
    main_account = models.Account(
        user_id=db_user.id,
        balance=100.0,
        main=True,
        closed=False,
        status=False,
        rib=f"FR{int(datetime.utcnow().timestamp())}{db_user.id}{uuid.uuid4().hex[:6]}",
        date=datetime.utcnow(),
    )
    db.add(main_account)
    db.commit()
    db.refresh(main_account)

    return {
        "user_id":db_user.id,
        "access_token": token,
        "token_type": "bearer",
        "user": UserOut.from_orm(db_user)
    }

# ----------------- LIST USERS -----------------
@router.get("/", response_model=list[UserOut])
def list_users(db: Session = Depends(get_session)):
    users = db.query(models.User).all()
    return [UserOut.from_orm(user) for user in users]

# ----------------- USER DETAILS -----------------
@router.get("/{user_id}", response_model=UserOut)
def user_details(user_id: int, db: Session = Depends(get_session)):
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return UserOut.from_orm(user)

# ----------------- LOGIN USER -----------------
@router.post("/login")
def login(user: LoginSchema, db: Session = Depends(get_session)):
    user_in_db = db.query(models.User).filter(models.User.email == user.email).first()
    if not user_in_db:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Email invalide")

    if not verify_password(user.password, user_in_db.password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Mot de passe incorrect")

    token = create_access_token({"sub": user_in_db.email, "user_id": user_in_db.id})
    return {"access_token": token, "token_type": "bearer"}

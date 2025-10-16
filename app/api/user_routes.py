from fastapi import APIRouter, HTTPException, Depends
from datetime import datetime
from app.db import models
from app.schemas.user_schemas import UserCreate, UserOut
from app.core.security import hash_password
from sqlmodel import Session
from app.db.database import get_session

import uuid

router = APIRouter(prefix="/users", tags=["Users"])

# <---------------- USERS ---------------->
@router.post("/", response_model=models.User)
def create_user_endpoint(user: UserCreate, db: Session = Depends(get_session)):
    """Create a new user with their main account"""
    # Check if email already exists
    if db.query(models.User).filter(models.User.email == user.email).first():
        raise HTTPException(status_code=400, detail="Email already registered")

    # Hash the user password (SHA256) - modification noted
    hashed_password = hash_password(user.password)
    # Create the user in DB
    db_user = models.User(name=user.name, email=user.email, password=hashed_password)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)

    # Create the main account for the user
    # Modification: added uuid to RIB to ensure uniqueness
    main_account = models.Account(
        user_id=db_user.id,
        balance=100.0,
        main=True,
        closed=False,
        status=False,
        rib=f"FR{int(datetime.utcnow().timestamp())}{db_user.id}{uuid.uuid4().hex[:6]}",  # Modification : added uuid for unique RIB
        date=datetime.utcnow()
    )

    db.add(main_account)
    db.commit()
    db.refresh(main_account)

    # Return the created user
    return db_user

@router.get("/", response_model=list[UserOut])
def list_users(db: Session = Depends(get_session)):
    """List all users without their passwords"""
    # Modification: use UserOut to hide password field
    users = db.query(models.User).all()
    return [UserOut.from_orm(user) for user in users]

@router.get("/{user_id}", response_model=UserOut)
def user_details(user_id: int, db: Session = Depends(get_session)):
    """Get the user's information"""
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    # Modification: use UserOut to hide password field
    return UserOut.from_orm(user)

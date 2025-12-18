from fastapi import APIRouter, HTTPException, Depends, status
from datetime import datetime, timezone
from sqlmodel import Session
from app.db import models
from app.schemas.user_schemas import UserCreate, UserOut, LoginSchema
from app.core.security import hash_password, verify_password, create_access_token
from app.db.database import get_session
import uuid

router = APIRouter(prefix="/users", tags=["Users"])

"""
User-related API endpoints.

This module contains all routes related to user management,
including registration, authentication, and user retrieval.
"""

# ----------------- CREATE USER -----------------
@router.post("/", response_model=dict)
def create_user_endpoint(user: UserCreate, db: Session = Depends(get_session)):
    """
    Create a new user and initialize a main bank account.

    This endpoint registers a new user, hashes the password,
    creates a default main account with an initial balance,
    and returns a JWT access token.

    Args:
        user (UserCreate): User registration data (name, email, password).
        db (Session): Database session dependency.

    Raises:
        HTTPException:
            - 400 if the email already exists.

    Returns:
        dict: Access token, token type, and user information.
    """
    existing_user = db.query(models.User).filter(models.User.email == user.email).first()

    if existing_user:
        raise HTTPException(status_code=400, detail="Email already exists")

    hashed_password = hash_password(user.password)
    db_user = models.User(name=user.name, email=user.email, password=hashed_password)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)

    main_account = models.Account(
        user_id=db_user.id,
        balance=100.0,
        main=True,
        closed=False,
        status=False,
        rib=f"FR{int(datetime.now(timezone.utc).timestamp())}{db_user.id}{uuid.uuid4().hex[:6]}",
        date=datetime.now(timezone.utc)
    )
    db.add(main_account)
    db.commit()
    db.refresh(main_account)

    access_token = create_access_token({"user_id": db_user.id})

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": UserOut.from_orm(db_user)
    }

# ----------------- LIST USERS -----------------
@router.get("/", response_model=list[UserOut])
def list_users(db: Session = Depends(get_session)):
    """
    Retrieve all users.

    Args:
        db (Session): Database session dependency.

    Returns:
        list[UserOut]: List of all registered users.
    """
    users = db.query(models.User).all()
    return [UserOut.from_orm(user) for user in users]

# ----------------- USER DETAILS -----------------
@router.get("/{user_id}", response_model=UserOut)
def user_details(user_id: int, db: Session = Depends(get_session)):
    """
    Retrieve details of a specific user by ID.

    Args:
        user_id (int): Unique identifier of the user.
        db (Session): Database session dependency.

    Raises:
        HTTPException:
            - 404 if the user does not exist.

    Returns:
        UserOut: User details.
    """
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return UserOut.from_orm(user)

# ----------------- LOGIN USER -----------------
@router.post("/login")
def login(user: LoginSchema, db: Session = Depends(get_session)):
    """
    Authenticate a user and return an access token.

    Args:
        user (LoginSchema): User login credentials (email and password).
        db (Session): Database session dependency.

    Raises:
        HTTPException:
            - 401 if email or password is invalid.

    Returns:
        dict: JWT access token and token type.
    """
    user_in_db = db.query(models.User).filter(models.User.email == user.email).first()
    if not user_in_db:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email"
        )

    if not verify_password(user.password, user_in_db.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid password"
        )

    token = create_access_token({"sub": user_in_db.email, "user_id": user_in_db.id})
    return {"access_token": token, "token_type": "bearer"}

from fastapi import APIRouter, HTTPException, Depends
from datetime import datetime
from app.db import models
from app.schemas.user_schemas import UserCreate, UserOut
from app.schemas.account_schemas import AccountCreate, AccountOut
from app.core.security import hash_password
from app.repositories.user_repository import UserRepo
from sqlmodel import Session
from app.db.database import engine, init_db, get_session

router = APIRouter(prefix="/users", tags=["Users"])

init_db()

    #<---------------- USERS ---------------->
@router.post("/", response_model=models.User)
def create_user_endpoint(user: UserCreate, db: Session = Depends(get_session)):
    """Create a new user with their main account"""
    # Check if email already exists
    if db.query(models.User).filter(models.User.email == user.email).first():
        raise HTTPException(status_code=400, detail="Email already registered")

    hashed_password = hash_password(user.password)
        #Create the user
    db_user = models.User(name=user.name, email=user.email, password=hashed_password)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)

    # Create the main account for the user
    main_account = models.Account(
        user_id=db_user.id,
        balance=100.0,
        main=True,
        closed=False,
        status=False,
        rib=f"FR{int(datetime.utcnow().timestamp())}{db_user.id}", # Generate RIB
        date=datetime.utcnow()
    )
    db.add(main_account)
    db.commit()
    db.refresh(main_account)

    return db_user

@router.get("/", response_model=list[UserOut])
def list_users(db: Session = Depends(get_session)):
    """List all users without their passwords"""
    return db.query(models.User).all()

@router.get("/{user_id}", response_model=UserOut)
def user_details(user_id: int, db: Session = Depends(get_session)):
    """Get the user's information"""
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

from fastapi import APIRouter
from app.schemas.user_schemas import UserCreate, UserOut
from app.schemas.account_schemas import AccountCreate, AccountOut
from app.core.security import hash_password
from app.db.database import users_db, accounts_db

router = APIRouter(prefix="/users", tags=["Users"])

@router.post("/", response_model=UserOut)
def create_user_endpoint(user: UserCreate):
    user_id = len(users_db) + 1
    hashed_password = hash_password(user.password)

    user_dict = user.dict()
    user_dict["id"] = user_id
    user_dict["password"] = hashed_password
    users_db.append(user_dict)

    # Création du compte lié
    account = AccountCreate(user_id=user_id, balance=0.0)
    account_dict = account.dict()
    account_dict["id"] = len(accounts_db) + 1
    accounts_db.append(account_dict)

    return user_dict

@router.get("/", response_model=list[UserOut])
def list_users_endpoint():
    return users_db

from fastapi import APIRouter
from app.schemas.user_schemas import UserCreate
from app.core.security import hash_password

router = APIRouter(prefix="/users", tags=["Users"])

users_db = []

@router.post("/", response_model=UserCreate)
def create_user_endpoint(user: UserCreate):
    hashed_password = hash_password(user.password)
    user_dict = user.dict()
    user_dict["password"] = hashed_password
    users_db.append(user_dict)
    return user_dict

@router.get("/", response_model=list[UserCreate])
def list_users_endpoint():
    return users_db

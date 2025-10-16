from fastapi import APIRouter
from app.schemas.user_schemas import UserCreate, UserOut
from app.schemas.account_schemas import AccountCreate, AccountOut
from app.core.security import hash_password
from app.db.database import users_db, accounts_db
from app.api.account_routes import generate_rib
from datetime import datetime

router = APIRouter(prefix="/users", tags=["Users"])

#<---------------- USERS ---------------->
@router.post("/", response_model=UserOut)
def create_user_endpoint(user: UserCreate):
    """Create a new user with their main account"""
    user_id = len(users_db) + 1 # ID auto-incremented => Take the last one of the user's list and add 1
    hashed_password = hash_password(user.password) # Hash the password

    #Create the user
    user_dict = user.dict() #transfor user object to dictionary
    user_dict["id"] = user_id
    user_dict["password"] = hashed_password
    users_db.append(user_dict) #add the user to the user's list

    # Create the main account for the user
    account = AccountCreate(user_id=user_id, balance=100.0, main=True) #Create an account object and initialize it => balance, user_id, main account
    account_dict = account.dict() #transfor account object to dictionary
    account_dict["id"] = len(accounts_db) + 1 # ID auto-incremented => Take the last one of the account's list and add 1
    account_dict["date"] = account.date or datetime.now().isoformat() #Add the current date if no date is provided
    account_dict["closed"] = False
    account_dict["status"] = False
    account_dict["rib"] = generate_rib() #Generate a RIB for the main account
    accounts_db.append(account_dict) #add the account to the account's list

    return user_dict

@router.get("/", response_model=list[UserOut])
def list_users_endpoint():
    """List all users without their passwords"""
    return users_db

@router.get("/{user_id}", response_model=UserOut)
def user_details(user_id: int):
    """Get the user's information"""
    user = next((u for u in users_db if u["id"] == user_id), None) #Look for the user in the list with his id

    #If there's no user return an error message
    if not user:
        return {"error": "User not found"}

    user_filtered = {k: v for k, v in user.items() if k != "password"}# Exclude password from the response

    return user_filtered



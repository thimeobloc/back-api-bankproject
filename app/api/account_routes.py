from fastapi import APIRouter
from app.schemas.account_schemas import AccountCreate
from app.db.database import accounts_db, balances_db

router = APIRouter(prefix="/accounts", tags=["Accounts"])

@router.get("/", response_model=list[AccountCreate])
def list_accounts_endpoint():
    return accounts_db


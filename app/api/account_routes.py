from fastapi import APIRouter, HTTPException
from app.schemas.account_schemas import*
from app.db.database import accounts_db, balances_db

router = APIRouter(prefix="/accounts", tags=["Accounts"])

@router.get("/", response_model=list[AccountCreate])
def list_accounts_endpoint():
    return accounts_db

@router.post("/", response_model=AccountOut)
def create_account_endpoint(account: AccountCreate):
    main_account = next((acc for acc in accounts_db if acc["user_id"] == account.user_id), None)
    if not main_account:
        raise HTTPException(status_code=404, detail="Account not found")

    account_id = len(accounts_db) + 1

    account_dict = account.dict()
    account_dict["id"] = account_id
    account_dict["balance"] = 0.0
    account_dict["main"] = False
    account_dict["user_id"] = main_account["user_id"]

    accounts_db.append(account_dict)

    return account_dict

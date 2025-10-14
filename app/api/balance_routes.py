from fastapi import APIRouter, HTTPException
from app.db.database import accounts_db, balances_db
from app.schemas.balance_schemas import *

router = APIRouter(prefix="/balances", tags=["Balances"])

@router.post("/deposit")
def deposit_endpoint(balance: depositCreate):
    account = next((a for a in accounts_db if a["id"] == balance.account_id), None)
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")

    account["balance"] += balance.amount

    balance_id = len(balances_db) + 1
    account.deposit.append({
        "id": balance_id,
        "account_id": balance.account_id,
        "amount": balance.amount,
        "type": "deposit",
        "date": balance.date
    })
    balances_db.append({
        "id": balance_id,
        "account_id": balance.account_id,
        "amount": balance.amount,
        "type": "deposit",
        "date": balance.date
    })

    return {"message": f"Deposit of {balance.amount}€ successful", "new_balance": account["balance"]}

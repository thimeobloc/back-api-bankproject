from fastapi import APIRouter, HTTPException
from app.db.database import accounts_db, balances_db
from app.schemas.balance_schemas import *
from app.core.security import amount_verification, enough_amount

router = APIRouter(prefix="/balances", tags=["Balances"])

@router.post("/deposit")
def deposit_endpoint(balance: depositCreate):
    account = next((account for account in accounts_db if account["id"] == balance.account_id), None)
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")

    if not amount_verification(balance.amount):
        return {"Le montant donné est invalide"}
    else:
        account["balance"] += balance.amount

        balance_id = len(balances_db) + 1
        account["deposit"].append({
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

@router.post("/transfer")
def transfer_endpoint(balance: transferCreate):
    sender = next((account for account in accounts_db if account["id"] == balance.from_account_id), None)
    recipient = next((account for account in accounts_db if account["id"] == balance.to_account_id), None)
    if not sender or not recipient:
        raise HTTPException(status_code=404, detail="Account not found")

    if not amount_verification(balance.amount):
        return {"Le montant donné est invalide"}

    if not enough_amount(balance.amount, sender["balance"]):
        return {"Monsieur, vous êtes pauvre"}
    else:
        recipient["balance"] += balance.amount
        sender["balance"] -= balance.amount

        balance_id = len(balances_db) + 1
        sender["transfer"].append({
            "id": balance_id,
            "from_account_id": balance.from_account_id,
            "to_account_id": balance.to_account_id,
            "account_id": balance.account_id,
            "amount": -balance.amount,
            "type": "transfer",
            "date": balance.date
        })
        recipient["transfer"].append({
            "id": balance_id,
            "from_account_id": balance.from_account_id,
            "to_account_id": balance.to_account_id,
            "account_id": balance.account_id,
            "amount": balance.amount,
            "type": "transfer",
            "date": balance.date
        })
        balances_db.append({
            "id": balance_id,
            "from_account_id": balance.from_account_id,
            "to_account_id": balance.to_account_id,
            "account_id": balance.account_id,
            "amount": balance.amount,
            "type": "deposit",
            "date": balance.date
        })

        return {"message": f"Deposit of {balance.amount}€ successful", "new_balance sender": sender["balance"], "new_balance recipient": recipient["balance"]}

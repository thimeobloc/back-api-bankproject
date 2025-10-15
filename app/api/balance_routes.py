from fastapi import APIRouter, HTTPException
from datetime import datetime
from app.db.database import accounts_db, balances_db
from app.schemas.balance_schemas import *
from app.core.security import amount_verification, enough_amount

router = APIRouter(prefix="/balances", tags=["Balances"])


# 🟢 DÉPÔT
@router.post("/deposit")
def deposit_endpoint(balance: depositCreate):
    account = next((a for a in accounts_db if a["id"] == balance.account_id), None)
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")

    if not amount_verification(balance.amount):
        return {"error": "Le montant donné est invalide"}

    account["balance"] += balance.amount

    balance_id = len(balances_db) + 1
    temp = {
        "id": balance_id,
        "account_id": balance.account_id,
        "amount": balance.amount,
        "type": "deposit",
        "date": balance.date or datetime.now().isoformat()  
    }

    account["deposit"].append(temp)
    balances_db.append(temp)

    return {
        "message": f"Deposit of {balance.amount}€ successful",
        "new_balance": account["balance"]
    }


# 🔁 TRANSFERT
@router.post("/transfer")
def transfer_endpoint(balance: transferCreate):
    sender = next((a for a in accounts_db if a["id"] == balance.from_account_id), None)
    recipient = next((a for a in accounts_db if a["id"] == balance.to_account_id), None)

    if not sender or not recipient:
        raise HTTPException(status_code=404, detail="Account not found")

    if sender["id"] == recipient["id"]:
        return {"error": "Transaction impossible (même compte)"}

    if not amount_verification(balance.amount):
        return {"error": "Le montant donné est invalide"}

    if not enough_amount(balance.amount, sender["balance"]):
        return {"error": "Monsieur, vous êtes pauvre"}

    # Transfert effectif
    sender["balance"] -= balance.amount
    recipient["balance"] += balance.amount

    balance_id = len(balances_db) + 1
    temp = {
        "id": balance_id,
        "from_account_id": balance.from_account_id,
        "to_account_id": balance.to_account_id,
        "amount": balance.amount,
        "type": "transfer",
        "date": balance.date or datetime.now().isoformat()  
    }

    sender["transfer"].append(temp)
    recipient["transfer"].append(temp)
    balances_db.append(temp)

    return {
        "message": f"Transfer of {balance.amount}€ successful",
        "new_balance_sender": sender["balance"],
        "new_balance_recipient": recipient["balance"]
    }


# 🔻 RETRAIT
@router.post("/withdraw")
def withdraw_endpoint(balance: withdrawCreate):
    account = next((a for a in accounts_db if a["id"] == balance.account_id), None)
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")

    if not amount_verification(balance.amount):
        return {"error": "Le montant donné est invalide"}

    if not enough_amount(balance.amount, account["balance"]):
        return {"error": "Monsieur, vous êtes pauvre"}

    account["balance"] -= balance.amount

    balance_id = len(balances_db) + 1
    temp = {
        "id": balance_id,
        "account_id": balance.account_id,
        "amount": balance.amount,
        "type": "withdraw",
        "date": balance.date or datetime.now().isoformat()  
    }

    account["withdraw"].append(temp)
    balances_db.append(temp)

    return {
        "message": f"Withdrawal of {balance.amount}€ successful",
        "new_balance": account["balance"]
    }

from fastapi import APIRouter, HTTPException
from datetime import datetime
from app.db.database import accounts_db, balances_db
from app.schemas.balance_schemas import *
from app.core.security import amount_verification, enough_amount

router = APIRouter(prefix="/balances", tags=["Balances"])



@router.post("/deposit")
def deposit_endpoint(balance: depositCreate):
    account = next((a for a in accounts_db if a["id"] == balance.account_id), None)
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")

    if not amount_verification(balance.amount):
        return {"error": "Le montant donné est invalide"}

    if account["closed"]:
        return {"error": "Transaction impossible l un des compte est fermé"}

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



@router.post("/transfer")
def transfer_endpoint(balance: transferCreate):
    sender = next((a for a in accounts_db if a["id"] == balance.from_account_id), None)
    recipient = next((a for a in accounts_db if a["id"] == balance.to_account_id), None)

    if not sender or not recipient:
        raise HTTPException(status_code=404, detail="Account not found")

    if sender["id"] == recipient["id"]:
        return {"error": "Transaction impossible (même compte)"}
    if sender["closed"] or recipient["closed"]:
        return {"error": "Transaction impossible l un des compte est fermé"}
    if not amount_verification(balance.amount):
        return {"error": "Le montant donné est invalide"}

    if not enough_amount(balance.amount, sender["balance"]):
        return {"error": "Monsieur, vous êtes pauvre"}

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



@router.post("/withdraw")
def withdraw_endpoint(balance: withdrawCreate):
    account = next((a for a in accounts_db if a["id"] == balance.account_id), None)
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")

    if not amount_verification(balance.amount):
        return {"error": "Le montant donné est invalide"}

    if not enough_amount(balance.amount, account["balance"]):
        return {"error": "Monsieur, vous êtes pauvre"}

    if account["closed"]:
        return {"error": "Transaction impossible l un des compte est fermé"}

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

@router.get("/transfers/{account_id}", response_model=list[transferCreate])
def list_transfers_by_account(account_id: int):
    transfers = [
        b for b in balances_db
        if b["type"] == "transfer"
        and (b["from_account_id"] == account_id or b["to_account_id"] == account_id)
    ]

    if not transfers:
        raise HTTPException(status_code=404, detail="Aucun transfert trouvé pour ce compte")

    transfers_sorted = sorted(transfers, key=lambda x: x["date"], reverse=True)

    return transfers_sorted

@router.get("/deposits/{account_id}", response_model=list[depositCreate])
def list_deposits_by_account(account_id: int):
    deposits = [
        b for b in balances_db
        if b["type"] == "deposit" and b["account_id"] == account_id
    ]

    if not deposits:
        raise HTTPException(status_code=404, detail="Aucun dépôt trouvé pour ce compte")

    deposits_sorted = sorted(deposits, key=lambda x: x["date"], reverse=True)

    return deposits_sorted

@router.get("/withdraws/{account_id}", response_model=list[withdrawCreate])
def list_withdraws_by_account(account_id: int):
    withdraws = [
        b for b in balances_db
        if b["type"] == "withdraw" and b["account_id"] == account_id
    ]

    if not withdraws:
        raise HTTPException(status_code=404, detail="Aucun retrait trouvé pour ce compte")

    withdraws_sorted = sorted(withdraws, key=lambda x: x["date"], reverse=True)

    return withdraws_sorted


@router.get("/transfer/{user_id}/{transfer_id}", response_model=transferCreate)
def get_transfer(transfer_id: int, user_id: int):
    transfer = next((b for b in balances_db if b["type"] == "transfer" and b["id"] == transfer_id), None)
    if not transfer:
        raise HTTPException(status_code=404, detail="Transfer not found")
    
    account_post = next((b for b in accounts_db if b["id"] == transfer["from_account_id"]), None)
    account_get = next((b for b in accounts_db if b["id"] == transfer["to_account_id"]), None)

    if account_get["user_id"] != user_id and account_post["user_id"] != user_id:
        raise HTTPException(status_code=404, detail="Account not found")

    return transfer
    
@router.get("/deposit/{user_id}/{deposit_id}", response_model=depositCreate)
def get_deposit(deposit_id: int, user_id: int):
    deposit = next((b for b in balances_db if b["type"] == "deposit" and b["id"] == deposit_id), None)
    if not deposit:
        raise HTTPException(status_code=404, detail="Deposit not found")
    
    account = next((b for b in accounts_db if b["id"] == deposit["account_id"]), None)

    if account["user_id"] != user_id:
        raise HTTPException(status_code=404, detail="Account not found")

    return deposit

@router.get("/withdraw/{user_id}/{withdraw_id}", response_model=withdrawCreate)
def get_withdraw(withdraw_id: int, user_id: int):
    withdraw = next((b for b in balances_db if b["type"] == "withdraw" and b["id"] == withdraw_id), None)
    if not withdraw:
        raise HTTPException(status_code=404, detail="Withdraw not found")
    
    account = next((b for b in accounts_db if b["id"] == withdraw["account_id"]), None)

    if account["user_id"] != user_id:
        raise HTTPException(status_code=404, detail="Account not found")

    return withdraw




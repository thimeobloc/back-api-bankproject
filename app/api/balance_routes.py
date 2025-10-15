from fastapi import APIRouter, HTTPException
from datetime import datetime
from app.db.database import accounts_db, balances_db
from app.schemas.balance_schemas import *
from app.core.security import amount_verification, enough_amount

router = APIRouter(prefix="/balances", tags=["Balances"])

deposit_counter = 0
withdraw_counter = 0
transfer_counter = 0


@router.post("/deposit")
def deposit_endpoint(balance: depositCreate):
    global deposit_counter
    account = next((a for a in accounts_db if a["id"] == balance.account_id), None)
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")
    if not amount_verification(balance.amount):
        return {"error": "Le montant donné est invalide"}

    account["balance"] += balance.amount

    deposit_counter += 1
    temp = {
        "id": deposit_counter,
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


@router.post("/withdraw")
def withdraw_endpoint(balance: withdrawCreate):
    global withdraw_counter
    account = next((a for a in accounts_db if a["id"] == balance.account_id), None)
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")
    if not amount_verification(balance.amount):
        return {"error": "Le montant donné est invalide"}
    if not enough_amount(balance.amount, account["balance"]):
        return {"error": "Monsieur, vous êtes pauvre"}

    account["balance"] -= balance.amount

    withdraw_counter += 1
    temp = {
        "id": withdraw_counter,
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


@router.post("/transfer")
def transfer_endpoint(balance: transferCreate):
    global transfer_counter
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

    sender["balance"] -= balance.amount
    recipient["balance"] += balance.amount

    transfer_counter += 1
    temp = {
        "id": transfer_counter,
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
        "new_balance_recipient": recipient["balance"],
        "transfer_id": transfer_counter
    }


@router.delete("/transfer_abort/{transfer_id}")
def abort_transfer(transfer_id: int):
    transfer = next((b for b in balances_db if b["type"] == "transfer" and b["id"] == transfer_id), None)
    if not transfer:
        raise HTTPException(status_code=404, detail="Transfer not found")

    transfer_date = datetime.fromisoformat(transfer["date"])
    if (datetime.now() - transfer_date).total_seconds() > 30:
        return {"error": "Le délai pour annuler le transfert est dépassé (30 secondes)"}

    sender = next((a for a in accounts_db if a["id"] == transfer["from_account_id"]), None)
    recipient = next((a for a in accounts_db if a["id"] == transfer["to_account_id"]), None)
    if not sender or not recipient:
        raise HTTPException(status_code=404, detail="Account not found")

    sender["balance"] += transfer["amount"]
    recipient["balance"] -= transfer["amount"]

    sender["transfer"] = [t for t in sender["transfer"] if t["id"] != transfer_id]
    recipient["transfer"] = [t for t in recipient["transfer"] if t["id"] != transfer_id]
    balances_db.remove(transfer)

    return {
        "message": f"Transfer of {transfer['amount']}€ aborted",
        "new_balance_sender": sender["balance"],
        "new_balance_recipient": recipient["balance"]
    }


@router.get("/transfer/{transfer_id}", response_model=transferCreate)
def get_transfer_by_id(transfer_id: int):
    transfer = next((b for b in balances_db if b["type"] == "transfer" and b["id"] == transfer_id), None)
    if not transfer:
        raise HTTPException(status_code=404, detail="Transfer not found")
    return transfer


@router.get("/transfers/{account_id}", response_model=list[transferCreate])
def list_transfers_by_account(account_id: int):
    transfers = [b for b in balances_db if b["type"] == "transfer" and (b["from_account_id"] == account_id or b["to_account_id"] == account_id)]
    return sorted(transfers, key=lambda x: x["date"], reverse=True)


@router.get("/deposits/{account_id}", response_model=list[depositCreate])
def list_deposits_by_account(account_id: int):
    deposits = [b for b in balances_db if b["type"] == "deposit" and b["account_id"] == account_id]
    return sorted(deposits, key=lambda x: x["date"], reverse=True)


@router.get("/withdraws/{account_id}", response_model=list[withdrawCreate])
def list_withdraws_by_account(account_id: int):
    withdraws = [b for b in balances_db if b["type"] == "withdraw" and b["account_id"] == account_id]
    return sorted(withdraws, key=lambda x: x["date"], reverse=True)

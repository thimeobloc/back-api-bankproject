from fastapi import APIRouter, HTTPException, BackgroundTasks
from datetime import datetime, timedelta
from time import sleep
from app.db.database import accounts_db, balances_db
from app.schemas.balance_schemas import *
from app.core.security import amount_verification, enough_amount

router = APIRouter(prefix="/balances", tags=["Balances"])

deposit_counter = 0
withdraw_counter = 0
transfer_counter = 0


# ---------------- DEPOSITS ----------------
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


# ---------------- WITHDRAWS ----------------
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


# ---------------- TRANSFERS ----------------
def complete_transfer_task(transfer_id: int):
    """Fonction pour compléter un transfert en arrière-plan."""
    transfer = next((b for b in balances_db if b["type"] == "transfer" and b["id"] == transfer_id), None)
    if not transfer or transfer["status"] != "pending":
        return

    recipient = next((a for a in accounts_db if a["id"] == transfer["to_account_id"]), None)
    if not recipient:
        return

    recipient["balance"] += transfer["amount"]
    recipient["transfer"].append(transfer)
    transfer["status"] = "completed"


def delayed_complete_transfer(transfer_id: int, delay: int = 30):
    sleep(delay)
    complete_transfer_task(transfer_id)


@router.post("/transfer")
def transfer_endpoint(balance: transferCreate, background_tasks: BackgroundTasks):
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

    transfer_counter += 1
    transfer_record = {
        "id": transfer_counter,
        "from_account_id": balance.from_account_id,
        "to_account_id": balance.to_account_id,
        "amount": balance.amount,
        "type": "transfer",
        "status": "pending",
        "date": balance.date or datetime.now().isoformat(),
        "expiry": (datetime.now() + timedelta(seconds=30)).isoformat()
    }

    sender["transfer"].append(transfer_record)
    balances_db.append(transfer_record)
    background_tasks.add_task(delayed_complete_transfer, transfer_id=transfer_counter, delay=30)

    return {
        "message": f"Transfer of {balance.amount}€ created (pending)",
        "new_balance_sender": sender["balance"],
        "transfer_id": transfer_counter,
        "status": "pending",
        "will_complete_at": transfer_record["expiry"]
    }


@router.post("/transfer_complete/{transfer_id}")
def complete_transfer(transfer_id: int):
    transfer = next((b for b in balances_db if b["type"] == "transfer" and b["id"] == transfer_id), None)
    if not transfer:
        raise HTTPException(status_code=404, detail="Transfer not found")
    if transfer["status"] != "pending":
        return {"error": "Transfer already completed or aborted"}

    recipient = next((a for a in accounts_db if a["id"] == transfer["to_account_id"]), None)
    if not recipient:
        raise HTTPException(status_code=404, detail="Recipient account not found")

    recipient["balance"] += transfer["amount"]
    recipient["transfer"].append(transfer)
    transfer["status"] = "completed"

    return {
        "message": f"Transfer of {transfer['amount']}€ completed",
        "new_balance_recipient": recipient["balance"]
    }


@router.delete("/transfer_abort/{user_id}/{transfer_id}")
def abort_transfer(user_id: int, transfer_id: int):
    transfer = next((b for b in balances_db if b["type"] == "transfer" and b["id"] == transfer_id), None)
    if not transfer:
        raise HTTPException(status_code=404, detail="Transfer not found")

    sender = next((a for a in accounts_db if a["id"] == transfer["from_account_id"]), None)
    if not sender:
        raise HTTPException(status_code=404, detail="Sender account not found")

    if sender["id"] != user_id:
        raise HTTPException(status_code=403, detail="You are not authorized to abort this transfer")

    if transfer["status"] != "pending":
        return {"error": "Transfer cannot be aborted (already completed)"}

    sender["balance"] += transfer["amount"]
    sender["transfer"] = [t for t in sender["transfer"] if t["id"] != transfer_id]
    balances_db.remove(transfer)

    return {
        "message": f"Transfer of {transfer['amount']}€ aborted",
        "new_balance_sender": sender["balance"]
    }


# ---------------- GETTERS ----------------
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

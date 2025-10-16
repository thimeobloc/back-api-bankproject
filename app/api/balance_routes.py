from fastapi import APIRouter, HTTPException, BackgroundTasks
from datetime import datetime, timedelta
from time import sleep
from app.db.database import accounts_db, balances_db, users_db
from app.schemas.balance_schemas import *
from app.core.security import amount_verification, enough_amount

router = APIRouter(prefix="/balances", tags=["Balances"])

deposit_counter = 0
withdraw_counter = 0
transfer_counter = 0


# ---------------- DEPOSITS ----------------
@router.post("/deposit")
def deposit_endpoint(balance: depositCreate):
    """Create a deposit transaction"""
    global deposit_counter
    account = next((a for a in accounts_db if a["id"] == balance.account_id), None) # Find the account with his id
    user = next((use for use in users_db if use["id"] == balance.user_id), None) #Look for the user with his id

    #If there's no user return an error message
    if not user:
        raise HTTPException(status_code=400, detail="L'utilisateur n'existe pas")

    #If there's no account return an error message
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")
    
    #Check if the account belongs to the user
    if account["user_id"] != balance.user_id:
        raise HTTPException(status_code=400, detail="Ce n\'est pas votre compte monsieur")
    
    #Check if the account is closed
    if account["closed"]:
        return {"error": "Transaction impossible : compte fermé"}
    
    #Check if the amount is positive
    if not amount_verification(balance.amount):
        return {"error": "Le montant donné est invalide"}

    account["balance"] += balance.amount #Add the deposit's amount to the account's balance

    deposit_counter += 1 #Increment the deposit counter to generate a unique ID

    #Create the deposit record
    temp = {
        "id": deposit_counter,
        "account_id": balance.account_id,
        "amount": balance.amount,
        "type": "deposit",
        "date": balance.date or datetime.now().isoformat()
    }

    account["deposit"].append(temp) #Add the deposit to the account's deposit list
    balances_db.append(temp) #Add the deposit to the global balances list

    return {
        "message": f"Deposit of {balance.amount}€ successful",
        "new_balance": account["balance"]
    }


@router.get("/deposits/{account_id}/{user_id}", response_model=list[depositCreate])
def list_deposits_by_account(account_id: int, user_id: int):
    """List all deposits for a specific account"""

    account = next((a for a in accounts_db if a["id"] == account_id), None) # Find the account with his id
    user = next((use for use in users_db if use["id"] == user_id), None) #Look for the user with his id

    #If there's no user return an error message
    if not user:
        raise HTTPException(status_code=400, detail="L'utilisateur n'existe pas")

    #If there's no account return an error message
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")
    
    #Check if the account belongs to the user
    if account["user_id"] != user_id:
        raise HTTPException(status_code=400, detail="Ce n\'est pas votre compte monsieur")
    
    #Check if the account is closed
    if account["closed"]:
        return {"error": "Action impossible : compte fermé"}
    
    deposits = account["deposit"]
    return sorted(deposits, key=lambda x: x["date"], reverse=True)




# ---------------- WITHDRAWS ----------------
@router.post("/withdraw")
def withdraw_endpoint(balance: withdrawCreate):
    """Create a withdraw transaction"""
    global withdraw_counter
    account = next((a for a in accounts_db if a["id"] == balance.account_id), None) # Find the account with his id
    user = next((use for use in users_db if use["id"] == balance.user_id), None) #Look for the user with his id

    #If there's no user return an error message
    if not user:
        raise HTTPException(status_code=400, detail="L'utilisateur n'existe pas")

    #If there's no account return an error message
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")
    
    #Check if the account belongs to the user
    if account["user_id"] != balance.user_id:
        raise HTTPException(status_code=400, detail="Ce n\'est pas votre compte monsieur")
    
    #Check if the account is closed
    if account["closed"]:
        return {"error": "Transaction impossible : compte fermé"}
    
    #Check if the amount is positive
    if not amount_verification(balance.amount):
        return {"error": "Le montant donné est invalide"}
    
    #Check if there's enough money on the account
    if not enough_amount(balance.amount, account["balance"]):
        return {"error": "Monsieur, vous êtes pauvre"}

    account["balance"] -= balance.amount #Subtract the withdraw's amount to the account's balance

    withdraw_counter += 1 #Increment the withdraw counter to generate a unique ID

    #Create the withdraw record
    temp = {
        "id": withdraw_counter,
        "account_id": balance.account_id,
        "amount": balance.amount,
        "type": "withdraw",
        "date": balance.date or datetime.now().isoformat()
    }

    account["withdraw"].append(temp) #Add the withdraw to the account's withdraw list
    balances_db.append(temp) #Add the withdraw  to the global balances list

    return {
        "message": f"Withdrawal of {balance.amount}€ successful",
        "new_balance": account["balance"]
    }


@router.get("/withdraws/{account_id}/{user_id}", response_model=list[withdrawCreate])
def list_withdraws_by_account(account_id: int, user_id: int):
    """List all withdraws for a specific account"""

    account = next((a for a in accounts_db if a["id"] == account_id), None) #Find the account with his id
    user = next((use for use in users_db if use["id"] == user_id), None) #Look for the user with his id

    #If there's no user return an error message
    if not user:
        raise HTTPException(status_code=400, detail="L'utilisateur n'existe pas")

    #If there's no account return an error message
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")
    
    #Check if the account belongs to the user
    if account["user_id"] != user_id:
        raise HTTPException(status_code=400, detail="Ce n\'est pas votre compte monsieur")
    
    #Check if the account is closed
    if account["closed"]:
        return {"error": "Action impossible : compte fermé"}
    
    withdraw = account["withdraw"]
    return sorted(withdraw, key=lambda x: x["date"], reverse=True)




# ---------------- TRANSFERS ----------------
from datetime import datetime
from time import sleep

def complete_transfer_task(transfer_id: int):
    """Complete a transfer immediately if it is pending"""
    # Find the transfer in balances_db
    transfer = next((t for t in balances_db if t["type"] == "transfer" and t["id"] == transfer_id), None)
    # If transfer not found or not pending, stop
    if not transfer or transfer["status"] != "pending":
        return
    # Find the recipient account
    recipient = next((a for a in accounts_db if a["id"] == transfer["to_account_id"]), None)

    # If recipient not found, mark transfer as failed
    if not recipient:
        transfer["status"] = "failed"
        return
    
    recipient["balance"] += transfer["amount"] #Add amount to recipient balance
    recipient["transfer"].append(transfer)  #Add the transfer to recipient's transfer list
    transfer["status"] = "completed" #Mark transfer as completed
    transfer["completed_at"] = datetime.now().isoformat() #Record the completion date and time


def delayed_complete_transfer(transfer_id: int, delay: int = 30):
    """Complete a transfer after a delay (blocking)"""

    # Wait for the given delay
    sleep(delay)
    # After delay, complete the transfer
    complete_transfer_task(transfer_id)



@router.post("/transfer")
def transfer_endpoint(balance: transferCreate, background_tasks: BackgroundTasks):
    """Create a transfer transaction"""
    global transfer_counter
    sender = next((acc for acc in accounts_db if acc["id"] == balance.from_account_id), None) #Find the sender's account with his id
    recipient = next((acc for acc in accounts_db if acc["rib"] == balance.rib), None) #Find the recipient's account with his id
    user = next((use for use in users_db if use["id"] == balance.user_id), None) #Look for the user with his id

    #If there's no user return an error message
    if not user:
        raise HTTPException(status_code=400, detail="L'utilisateur n'existe pas")
    
    #Check if the sender's account belongs to the user
    if sender["user_id"] != balance.user_id:
        raise HTTPException(status_code=400, detail="Ce n\'est pas votre compte monsieur")

    #If there's no sender's account or recipient's account return an error message
    if not sender or not recipient:
        raise HTTPException(status_code=404, detail="Account not found")
    
    #Check if the sender's account is different from the recipient's account
    if sender["id"] == recipient["id"]:
        return {"error": "Transaction impossible (même compte)"}
    
    #Check if the sender's account or the recipient's account is not closed
    if sender["closed"] or recipient["closed"]:
        return {"error": "Transaction impossible : compte fermé"}
    
    #Check if the amount is positive
    if not amount_verification(balance.amount):
        return {"error": "Le montant donné est invalide"}
    
    #Check if there's enough money on the account
    if not enough_amount(balance.amount, sender["balance"]):
        return {"error": "Monsieur, vous êtes pauvre"}

    sender["balance"] -= balance.amount #Subtract the transfer's amount to the sender's account balance

    transfer_counter += 1 #Increment the transfer counter to generate a unique ID

    #Create the transfer record
    transfer_record = {
        "id": transfer_counter,
        "from_account_id": balance.from_account_id,
        "to_account_id": balance.to_account_id,
        "amount": balance.amount,
        "type": "transfer",
        "status": "pending",
        "date": balance.date or datetime.now().isoformat(),
        "will_complete_at": (datetime.now() + timedelta(seconds=30)).isoformat()
    }

    balances_db.append(transfer_record) #Add the transfer to the global balances list
    sender["transfer"].append(transfer_record) #Add the transfer to the sender's account transfer list

    # Schedule the transfer completion after 30 seconds
    background_tasks.add_task(delayed_complete_transfer, transfer_id=transfer_counter, delay=30)

    return {
        "message": f"Transfer of {balance.amount}€ created. Will complete automatically in 30 seconds",
        "transfer_id": transfer_counter,
        "status": "pending",
        "new_balance_sender": sender["balance"],
        "will_complete_at": transfer_record["will_complete_at"]
    }


@router.delete("/transfer_abort/{user_id}/{transfer_id}")
def abort_transfer(user_id: int, transfer_id: int):
    """Abort a pending transfer"""
    transfer = next((b for b in balances_db if b["type"] == "transfer" and b["id"] == transfer_id), None) # Find the transfer with its id

    #If there's no transfer return an error message
    if not transfer:
        raise HTTPException(status_code=404, detail="Transfer not found")

    sender = next((a for a in accounts_db if a["id"] == transfer["from_account_id"]), None) #Find the sender's account with his id
    user = next((use for use in users_db if use["id"] == user_id), None) #Look for the user with his id

    #If there's no user return an error message
    if not user:
        raise HTTPException(status_code=400, detail="L'utilisateur n'existe pas")

    #If there's no sender's account return an error message
    if not sender:
        raise HTTPException(status_code=404, detail="Sender account not found")

    #Check if the sender's account belongs to the user
    if sender["id"] != user_id:
        raise HTTPException(status_code=403, detail="You are not authorized to abort this transfer")

    #Check if the transfer is still pending
    if transfer["status"] != "pending":
        return {"error": "Transfer cannot be aborted (already completed)"}

    # Abort the transfer
    sender["balance"] += transfer["amount"] #Add the transfer amount to the sender's account
    sender["transfer"] = [t for t in sender["transfer"] if t["id"] != transfer_id] #Remove the transfer from the sender's account transfer list
    balances_db.remove(transfer) #Remove the transfer from the global balances list

    return {
        "message": f"Transfer of {transfer['amount']}€ aborted",
        "new_balance_sender": sender["balance"]
    }


@router.get("/transfers/{account_id}/{user_id}", response_model=list[transferCreate])
def list_transfers_by_account(account_id: int, user_id: int):
    account = next((a for a in accounts_db if a["id"] == account_id), None) # Find the account with his id
    user = next((use for use in users_db if use["id"] == user_id), None) #Look for the user with his id

    #If there's no user return an error message
    if not user:
        raise HTTPException(status_code=400, detail="L'utilisateur n'existe pas")

    #If there's no account return an error message
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")
    
    #Check if the account belongs to the user
    if account["user_id"] != user_id:
        raise HTTPException(status_code=400, detail="Ce n\'est pas votre compte monsieur")
    
    #Check if the account is closed
    if account["closed"]:
        return {"error": "Action impossible : compte fermé"}
    
    transfers = account["transfer"]
    return sorted(transfers, key=lambda x: x["date"], reverse=True)







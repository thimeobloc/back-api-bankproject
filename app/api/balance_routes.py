from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from datetime import datetime
from time import sleep
from app.db import models
from app.schemas.balance_schemas import depositCreate, withdrawCreate, transferCreate
from sqlmodel import Session
from app.db.database import users_db, accounts_db, balances_db, get_session, init_db
from app.core.security import amount_verification, enough_amount

router = APIRouter(prefix="/balances", tags=["Balances"])

deposit_counter = 0
withdraw_counter = 0
transfer_counter = 0

init_db()

# ---------------- DEPOSITS ----------------
@router.post("/deposit")
def deposit_endpoint(balance: depositCreate, db: Session = Depends(get_session)):
    user = db.query(models.User).filter(models.User.id == balance.user_id).first()
    if not user:
        raise HTTPException(status_code=400, detail="L'utilisateur n'existe pas")

    account = db.query(models.Account).filter(models.Account.id == balance.account_id).first()
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")

    if account.user_id != balance.user_id:
        raise HTTPException(status_code=400, detail="Ce n'est pas votre compte monsieur")

    if account.closed:
        raise HTTPException(status_code=400, detail="Transaction impossible : compte fermé")

    if not amount_verification(balance.amount):
        raise HTTPException(status_code=400, detail="Le montant donné est invalide")

    account.balance += balance.amount

    deposit = models.Deposit(
        account_id=account.id,
        amount=balance.amount,
        status="pending",
        date=datetime.utcnow()
    )

    db.add(deposit)
    db.commit()
    db.refresh(deposit)
    db.refresh(account)

    return {
        "message": f"Deposit of {balance.amount}€ successful",
        "new_balance": account.balance,
        "deposit_id": deposit.id
    }

@router.get("/deposits/{account_id}/{user_id}", response_model=list[models.Deposit])
def list_deposits_by_account(account_id: int, user_id: int, db: Session = Depends(get_session)):
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=400, detail="L'utilisateur n'existe pas")

    account = db.query(models.Account).filter(models.Account.id == account_id).first()
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")

    if account.user_id != user_id:
        raise HTTPException(status_code=400, detail="Ce n'est pas votre compte monsieur")

    if account.closed:
        raise HTTPException(status_code=400, detail="Action impossible : compte fermé")

    deposits = account.deposits
    return sorted(deposits, key=lambda x: x.date, reverse=True)


# ---------------- WITHDRAWS ----------------
@router.post("/withdraw")
def withdraw_endpoint(balance: withdrawCreate, users_db=Depends(users_db), accounts_db=Depends(accounts_db), db: Session = Depends(get_session)):
    global withdraw_counter

    user = next((u for u in users_db if u.id == balance.user_id), None)
    if not user:
        raise HTTPException(status_code=400, detail="L'utilisateur n'existe pas")

    account = next((a for a in accounts_db if a.id == balance.account_id), None)
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")

    if account.user_id != balance.user_id:
        raise HTTPException(status_code=400, detail="Ce n'est pas votre compte monsieur")

    if account.closed:
        raise HTTPException(status_code=400, detail="Transaction impossible : compte fermé")

    if not amount_verification(balance.amount):
        raise HTTPException(status_code=400, detail="Le montant donné est invalide")

    if not enough_amount(balance.amount, account.balance):
        raise HTTPException(status_code=400, detail="Monsieur, vous êtes pauvre")

    account.balance -= balance.amount
    withdraw_counter += 1

    withdraw = models.Withdraw(
        account_id=account.id,
        amount=balance.amount,
        status="pending",
        date=datetime.utcnow()
    )

    db.add(withdraw)
    db.commit()
    db.refresh(withdraw)

    account.withdraws.append(withdraw)

    return {
        "message": f"Withdrawal of {balance.amount}€ successful",
        "new_balance": account.balance
    }

@router.get("/withdraws/{account_id}/{user_id}", response_model=list[models.Withdraw])
def list_withdraws_by_account(account_id: int, user_id: int, users_db=Depends(users_db), accounts_db=Depends(accounts_db)):
    account = next((a for a in accounts_db if a.id == account_id), None)
    user = next((u for u in users_db if u.id == user_id), None)

    if not user:
        raise HTTPException(status_code=400, detail="L'utilisateur n'existe pas")
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")
    if account.user_id != user_id:
        raise HTTPException(status_code=400, detail="Ce n'est pas votre compte monsieur")
    if account.closed:
        raise HTTPException(status_code=400, detail="Action impossible : compte fermé")

    withdraws = account.withdraws
    return sorted(withdraws, key=lambda x: x.date, reverse=True)


# ---------------- TRANSFERS ----------------
def complete_transfer_task(transfer_id: int):
    with next(get_session()) as db:
        transfer = db.query(models.Transfer).filter(models.Transfer.id == transfer_id).first()
        if not transfer or transfer.status != "pending":
            return
        recipient = db.query(models.Account).filter(models.Account.id == transfer.to_account_id).first()
        if not recipient:
            transfer.status = "failed"
            db.commit()
            return
        recipient.balance += transfer.amount
        transfer.status = "completed"
        transfer.completed_at = datetime.utcnow()
        db.add(recipient)
        db.add(transfer)
        db.commit()



def delayed_complete_transfer(transfer_id: int, delay: int = 30):
    sleep(delay)
    complete_transfer_task(transfer_id)


@router.post("/transfer")
def transfer_endpoint(balance: transferCreate, background_tasks: BackgroundTasks, users_db=Depends(users_db), accounts_db=Depends(accounts_db), db: Session = Depends(get_session)):
    global transfer_counter

    sender = next((a for a in accounts_db if a.id == balance.from_account_id), None)
    recipient = next((a for a in accounts_db if a.id == balance.to_account_id), None)
    user = next((u for u in users_db if u.id == sender.user_id), None)

    if not user:
        raise HTTPException(status_code=400, detail="L'utilisateur n'existe pas")
    if not sender or not recipient:
        raise HTTPException(status_code=404, detail="Account not found")
    if sender.user_id != user.id:
        raise HTTPException(status_code=400, detail="Ce n'est pas votre compte monsieur")
    if sender.id == recipient.id:
        raise HTTPException(status_code=400, detail="Transaction impossible (même compte)")
    if sender.closed or recipient.closed:
        raise HTTPException(status_code=400, detail="Transaction impossible : compte fermé")
    if not amount_verification(balance.amount):
        raise HTTPException(status_code=400, detail="Le montant donné est invalide")
    if not enough_amount(balance.amount, sender.balance):
        raise HTTPException(status_code=400, detail="Monsieur, vous êtes pauvre")

    sender.balance -= balance.amount
    transfer_counter += 1

    transfer = models.Transfer(
        from_account_id=sender.id,
        to_account_id=recipient.id,
        amount=balance.amount,
        status="pending",
        type="transfer",
        date=datetime.utcnow()
    )

    db.add(transfer)
    db.commit()
    db.refresh(transfer)

    sender.transfers_sent.append(transfer)

    background_tasks.add_task(delayed_complete_transfer, transfer_id=transfer.id, delay=30)


    return {
        "message": f"Transfer of {balance.amount}€ created. Will complete automatically in 30 seconds",
        "transfer_id": transfer_counter,
        "status": "pending",
        "new_balance_sender": sender.balance
    }


@router.delete("/transfer_abort/{from_account_id}/{to_account_id}")
def abort_transfer(from_account_id: int, to_account_id: int, db: Session = Depends(get_session)):
    # Cherche un transfert en cours (pending) pour ces deux comptes
    transfer = db.query(models.Transfer).filter(
        models.Transfer.from_account_id == from_account_id,
        models.Transfer.to_account_id == to_account_id,
        models.Transfer.status == "pending"
    ).first()

    if not transfer:
        raise HTTPException(status_code=404, detail="No pending transfer found for these accounts")

    # Annule le transfert
    transfer.status = "aborted"

    # Rembourse l'argent à l'expéditeur
    sender = db.query(models.Account).filter(models.Account.id == from_account_id).first()
    sender.balance += transfer.amount

    # Actualiser la bdd
    db.add(transfer)
    db.add(sender)
    db.commit()
    db.refresh(transfer)
    db.refresh(sender)

    return {"message": "Transfer aborted"}

@router.get("/transfers/user/{user_id}")
def get_user_transfers(user_id: int, db: Session = Depends(get_session)):
    # Récupère tous les comptes de l'utilisateur
    accounts = db.query(models.Account).filter(models.Account.user_id == user_id).all()
    account_ids = [acc.id for acc in accounts]

    # Récupère tous les transferts envoyés ou reçus par ces comptes
    transfers = db.query(models.Transfer).filter(
        (models.Transfer.from_account_id.in_(account_ids)) |
        (models.Transfer.to_account_id.in_(account_ids))
    ).all()

    return [
        {
            "transfer_id": t.id,
            "from_account_id": t.from_account_id,
            "to_account_id": t.to_account_id,
            "amount": t.amount,
            "status": t.status,
            "date": t.date
        }
        for t in transfers
    ]

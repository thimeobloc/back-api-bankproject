from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from datetime import datetime, timezone
from time import sleep
from sqlmodel import Session, select
from app.db import models
from app.schemas.balance_schemas import DepositCreate, WithdrawCreate, TransferByRIB
from app.db.database import get_session
from app.core.security import amount_verification, enough_amount, oauth2_scheme, SECRET_KEY, ALGORITHM
from jose import jwt, JWTError

router = APIRouter(prefix="/balances", tags=["Balances"])

# ---------------------------
# Constants
# ---------------------------
ACCESS_DENIED = "Accès refusé"
ACCOUNT_NOT_FOUND = "Compte non trouvé"
NOT_YOUR_ACCOUNT = "Ce n'est pas votre compte"
ACCOUNT_CLOSED = "Compte fermé"
INVALID_AMOUNT = "Montant invalide"
INSUFFICIENT_BALANCE = "Solde insuffisant"
SAME_ACCOUNT_TRANSFER = "Transfert impossible (même compte)"
TRANSFER_NOT_FOUND = "Transfert non trouvé ou déjà traité"

# ---------------------------
# JWT Helper
# ---------------------------
def get_current_user(token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: int = payload.get("user_id")
        if user_id is None:
            raise HTTPException(status_code=401, detail="Invalid token")
        return user_id
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

# ---------------------------
# Deposits
# ---------------------------
@router.post("/deposit")
def deposit_endpoint(balance: DepositCreate, current_user: int = Depends(get_current_user), db: Session = Depends(get_session)):
    if balance.user_id != current_user:
        raise HTTPException(status_code=403, detail=ACCESS_DENIED)
    
    account = db.get(models.Account, balance.account_id)
    if not account:
        raise HTTPException(status_code=404, detail=ACCOUNT_NOT_FOUND)
    if account.user_id != current_user:
        raise HTTPException(status_code=403, detail=NOT_YOUR_ACCOUNT)
    if account.closed:
        raise HTTPException(status_code=400, detail=ACCOUNT_CLOSED)
    if not amount_verification(balance.amount):
        raise HTTPException(status_code=400, detail=INVALID_AMOUNT)
    
    account.balance += balance.amount
    deposit = models.Deposit(
        account_id=account.id,
        amount=balance.amount,
        type="deposit",
        date=datetime.now(timezone.utc)
    )
    db.add(deposit)
    db.commit()
    db.refresh(deposit)
    db.refresh(account)

    return {"message": f"Dépot de {balance.amount}€ effectué", "new_balance": account.balance, "deposit_id": deposit.id}

@router.get("/deposits/{account_id}", response_model=list[models.Deposit])
def list_deposits(account_id: int, current_user: int = Depends(get_current_user), db: Session = Depends(get_session)):
    account = db.get(models.Account, account_id)
    if not account or account.user_id != current_user:
        raise HTTPException(status_code=403, detail=ACCESS_DENIED)
    if account.closed:
        raise HTTPException(status_code=400, detail=ACCOUNT_CLOSED)

    deposits = db.exec(
        select(models.Deposit)
        .where(models.Deposit.account_id == account_id)
        .order_by(models.Deposit.date.desc())
    ).all()
    return deposits

# ---------------------------
# Withdraws
# ---------------------------
@router.post("/withdraw")
def withdraw_endpoint(balance: WithdrawCreate, current_user: int = Depends(get_current_user), db: Session = Depends(get_session)):
    if balance.user_id != current_user:
        raise HTTPException(status_code=403, detail=ACCESS_DENIED)
    
    account = db.get(models.Account, balance.account_id)
    if not account:
        raise HTTPException(status_code=404, detail=ACCOUNT_NOT_FOUND)
    if account.user_id != current_user:
        raise HTTPException(status_code=403, detail=NOT_YOUR_ACCOUNT)
    if account.closed:
        raise HTTPException(status_code=400, detail=ACCOUNT_CLOSED)
    if not amount_verification(balance.amount):
        raise HTTPException(status_code=400, detail=INVALID_AMOUNT)
    if not enough_amount(balance.amount, account.balance):
        raise HTTPException(status_code=400, detail=INSUFFICIENT_BALANCE)
    
    account.balance -= balance.amount
    withdraw = models.Withdraw(
        account_id=account.id,
        amount=balance.amount,
        type="withdraw",
        date=datetime.now(timezone.utc)
    )
    db.add(withdraw)
    db.commit()
    db.refresh(withdraw)
    db.refresh(account)

    return {"message": f"Retrait de {balance.amount}€ effectué", "new_balance": account.balance}

@router.get("/withdraws/{account_id}", response_model=list[models.Withdraw])
def list_withdraws(account_id: int, current_user: int = Depends(get_current_user), db: Session = Depends(get_session)):
    account = db.get(models.Account, account_id)
    if not account or account.user_id != current_user:
        raise HTTPException(status_code=403, detail=ACCESS_DENIED)
    if account.closed:
        raise HTTPException(status_code=400, detail=ACCOUNT_CLOSED)

    withdraws = db.exec(
        select(models.Withdraw)
        .where(models.Withdraw.account_id == account_id)
        .order_by(models.Withdraw.date.desc())
    ).all()
    return withdraws

# ---------------------------
# Transfers
# ---------------------------
def complete_transfer_task(db: Session, transfer_id: int):
    transfer = db.get(models.Transfer, transfer_id)
    if not transfer or transfer.status != "pending":
        return
    recipient = db.get(models.Account, transfer.to_account_id)
    if not recipient:
        transfer.status = "failed"
        db.commit()
        return
    recipient.balance += transfer.amount
    transfer.status = "completed"
    db.add_all([recipient, transfer])
    db.commit()

def delayed_complete_transfer(transfer_id: int, db: Session, delay: int = 30):
    sleep(delay)
    complete_transfer_task(db, transfer_id)

@router.post("/transfer")
def transfer_endpoint(balance: TransferByRIB, background_tasks: BackgroundTasks, current_user: int = Depends(get_current_user), db: Session = Depends(get_session)):
    recipient = db.exec(select(models.Account).where(models.Account.rib == balance.to_rib)).first()
    sender = db.get(models.Account, balance.from_account_id)
    
    if not sender or not recipient:
        raise HTTPException(status_code=404, detail=ACCOUNT_NOT_FOUND)
    if sender.user_id != current_user:
        raise HTTPException(status_code=403, detail=NOT_YOUR_ACCOUNT)
    if sender.id == recipient.id:
        raise HTTPException(status_code=400, detail=SAME_ACCOUNT_TRANSFER)
    if sender.closed or recipient.closed:
        raise HTTPException(status_code=400, detail=ACCOUNT_CLOSED)
    if not amount_verification(balance.amount):
        raise HTTPException(status_code=400, detail=INVALID_AMOUNT)
    if not enough_amount(balance.amount, sender.balance):
        raise HTTPException(status_code=400, detail=INSUFFICIENT_BALANCE)
    
    sender.balance -= balance.amount
    transfer = models.Transfer(
        from_account_id=sender.id,
        to_account_id=recipient.id,
        amount=balance.amount,
        type="transfer",
        status="pending",
        date=datetime.now(timezone.utc)
    )
    db.add(transfer)
    db.commit()
    db.refresh(transfer)
    db.refresh(sender)

    background_tasks.add_task(delayed_complete_transfer, transfer_id=transfer.id, db=db, delay=30)

    return {"message": f"Transfert de {balance.amount}€ initié", "transfer_id": transfer.id, "status": "pending", "new_balance_sender": sender.balance}

@router.delete("/transfer_abort/{transfer_id}")
def abort_transfer(transfer_id: int, current_user: int = Depends(get_current_user), db: Session = Depends(get_session)):
    transfer = db.get(models.Transfer, transfer_id)
    if not transfer or transfer.status != "pending":
        raise HTTPException(status_code=404, detail=TRANSFER_NOT_FOUND)
    sender = db.get(models.Account, transfer.from_account_id)
    if sender.user_id != current_user:
        raise HTTPException(status_code=403, detail=ACCESS_DENIED)
    
    sender.balance += transfer.amount
    transfer.status = "aborted"
    db.add_all([sender, transfer])
    db.commit()
    return {"message": "Transfert annulé"}

@router.get("/transfers")
def get_user_transfers(current_user: int = Depends(get_current_user), db: Session = Depends(get_session)):
    accounts = db.exec(select(models.Account).where(models.Account.user_id == current_user)).all()
    account_ids = [acc.id for acc in accounts]
    transfers = db.exec(
        select(models.Transfer)
        .where(
            (models.Transfer.from_account_id.in_(account_ids)) |
            (models.Transfer.to_account_id.in_(account_ids))
        )
        .order_by(models.Transfer.date.desc())
    ).all()
    return transfers

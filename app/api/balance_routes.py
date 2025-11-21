from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from datetime import datetime
from time import sleep
from sqlmodel import Session, select
from app.db import models
from app.schemas.balance_schemas import depositCreate, withdrawCreate, transferCreate
from app.db.database import get_session
from app.core.security import amount_verification, enough_amount, oauth2_scheme, SECRET_KEY, ALGORITHM
from jose import jwt, JWTError

router = APIRouter(prefix="/balances", tags=["Balances"])

# ----------------- JWT Helper -----------------
def get_current_user(token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: int = payload.get("user_id")
        if user_id is None:
            raise HTTPException(status_code=401, detail="Invalid token")
        return user_id
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

# ---------------- DEPOSITS ----------------
@router.post("/deposit")
def deposit_endpoint(balance: depositCreate, current_user: int = Depends(get_current_user), db: Session = Depends(get_session)):
    if balance.user_id != current_user:
        raise HTTPException(status_code=403, detail="Accès refusé")
    
    account = db.get(models.Account, balance.account_id)
    if not account:
        raise HTTPException(status_code=404, detail="Compte non trouvé")
    if account.user_id != current_user:
        raise HTTPException(status_code=403, detail="Ce n'est pas votre compte")
    if account.closed:
        raise HTTPException(status_code=400, detail="Compte fermé")
    if not amount_verification(balance.amount):
        raise HTTPException(status_code=400, detail="Montant invalide")
    
    account.balance += balance.amount
    deposit = models.Deposit(
        account_id=account.id,
        amount=balance.amount,
        type="deposit",
        date=datetime.utcnow()
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
        raise HTTPException(status_code=403, detail="Accès refusé")
    if account.closed:
        raise HTTPException(status_code=400, detail="Compte fermé")

    deposits = db.exec(select(models.Deposit).where(models.Deposit.account_id == account_id).order_by(models.Deposit.date.desc())).all()
    return deposits

# ---------------- WITHDRAWS ----------------
@router.post("/withdraw")
def withdraw_endpoint(balance: withdrawCreate, current_user: int = Depends(get_current_user), db: Session = Depends(get_session)):
    if balance.user_id != current_user:
        raise HTTPException(status_code=403, detail="Accès refusé")
    
    account = db.get(models.Account, balance.account_id)
    if not account:
        raise HTTPException(status_code=404, detail="Compte non trouvé")
    if account.user_id != current_user:
        raise HTTPException(status_code=403, detail="Ce n'est pas votre compte")
    if account.closed:
        raise HTTPException(status_code=400, detail="Compte fermé")
    if not amount_verification(balance.amount):
        raise HTTPException(status_code=400, detail="Montant invalide")
    if not enough_amount(balance.amount, account.balance):
        raise HTTPException(status_code=400, detail="Solde insuffisant")

    account.balance -= balance.amount
    withdraw = models.Withdraw(
        account_id=account.id,
        amount=balance.amount,
        type="withdraw",
        date=datetime.utcnow()
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
        raise HTTPException(status_code=403, detail="Accès refusé")
    if account.closed:
        raise HTTPException(status_code=400, detail="Compte fermé")

    withdraws = db.exec(select(models.Withdraw).where(models.Withdraw.account_id == account_id).order_by(models.Withdraw.date.desc())).all()
    return withdraws

# ---------------- TRANSFERS ----------------
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
    transfer.completed_at = datetime.utcnow()
    db.add_all([recipient, transfer])
    db.commit()

def delayed_complete_transfer(transfer_id: int, db: Session, delay: int = 30):
    sleep(delay)
    complete_transfer_task(db, transfer_id)

@router.post("/transfer")
def transfer_endpoint(balance: transferCreate, background_tasks: BackgroundTasks, current_user: int = Depends(get_current_user), db: Session = Depends(get_session)):
    sender = db.get(models.Account, balance.from_account_id)
    recipient = db.get(models.Account, balance.to_account_id)
    
    if not sender or not recipient:
        raise HTTPException(status_code=404, detail="Compte non trouvé")
    if sender.user_id != current_user:
        raise HTTPException(status_code=403, detail="Ce n'est pas votre compte")
    if sender.id == recipient.id:
        raise HTTPException(status_code=400, detail="Transfert impossible (même compte)")
    if sender.closed or recipient.closed:
        raise HTTPException(status_code=400, detail="Compte fermé")
    if not amount_verification(balance.amount):
        raise HTTPException(status_code=400, detail="Montant invalide")
    if not enough_amount(balance.amount, sender.balance):
        raise HTTPException(status_code=400, detail="Solde insuffisant")

    # ---------------- Vérification bénéficiaire ----------------
    beneficiary = db.exec(
        select(models.Beneficiary)
        .where(models.Beneficiary.account_id == sender.id)
        .where(models.Beneficiary.rib == recipient.rib)
    ).first()
    if not beneficiary:
        raise HTTPException(status_code=403, detail="Destinataire non autorisé (ajoutez-le comme bénéficiaire d'abord)")

    sender.balance -= balance.amount
    transfer = models.Transfer(
        from_account_id=sender.id,
        to_account_id=recipient.id,
        amount=balance.amount,
        type="transfer",
        status="pending",
        date=datetime.utcnow()
    )
    db.add(transfer)
    db.commit()
    db.refresh(transfer)
    db.refresh(sender)

    # Tâche en arrière-plan pour compléter le transfert
    background_tasks.add_task(delayed_complete_transfer, transfer_id=transfer.id, db=db, delay=30)

    return {"message": f"Transfert de {balance.amount}€ initié", "transfer_id": transfer.id, "status": "pending", "new_balance_sender": sender.balance}

@router.delete("/transfer_abort/{transfer_id}")
def abort_transfer(transfer_id: int, current_user: int = Depends(get_current_user), db: Session = Depends(get_session)):
    transfer = db.get(models.Transfer, transfer_id)
    if not transfer or transfer.status != "pending":
        raise HTTPException(status_code=404, detail="Transfert non trouvé ou déjà traité")
    sender = db.get(models.Account, transfer.from_account_id)
    if sender.user_id != current_user:
        raise HTTPException(status_code=403, detail="Accès refusé")
    
    sender.balance += transfer.amount
    transfer.status = "aborted"
    db.add_all([sender, transfer])
    db.commit()
    return {"message": "Transfert annulé"}

@router.get("/transfers")
def get_user_transfers(current_user: int = Depends(get_current_user), db: Session = Depends(get_session)):
    accounts = db.exec(select(models.Account).where(models.Account.user_id == current_user)).all()
    account_ids = [acc.id for acc in accounts]
    transfers = db.exec(select(models.Transfer).where(
        (models.Transfer.from_account_id.in_(account_ids)) | 
        (models.Transfer.to_account_id.in_(account_ids))
    ).order_by(models.Transfer.date.desc())).all()
    return transfers

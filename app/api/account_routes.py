from fastapi import APIRouter, HTTPException, Depends
from datetime import datetime
from sqlmodel import Session
from app.db import models
from app.db.database import get_session, init_db
from app.core.security import oauth2_scheme, SECRET_KEY, ALGORITHM
from jose import jwt, JWTError
import uuid
from app.schemas.account_schemas import *

router = APIRouter(prefix="/accounts", tags=["Accounts"])
init_db()

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

# ----------------- Helpers -----------------
def generate_rib(user_id: int) -> str:
    return f"FR{int(datetime.utcnow().timestamp())}{user_id}{uuid.uuid4().hex[:6]}"

# ----------------- ACCOUNTS -----------------
@router.get("/", response_model=list[models.Account])
def list_accounts(current_user: int = Depends(get_current_user), db: Session = Depends(get_session)):
    """Liste tous les comptes de l'utilisateur"""
    return db.query(models.Account).filter(models.Account.user_id == current_user).all()

@router.get("/myaccounts/", response_model=list[models.Account])
def view_accounts(db: Session = Depends(get_session), current_user: int = Depends(get_current_user)):
    """Liste uniquement les comptes actifs (non fermés)"""
    accounts = db.query(models.Account).filter(
        models.Account.user_id == current_user,
        models.Account.closed == False
    ).order_by(models.Account.date.desc()).all()
    return accounts

@router.post("/", response_model=models.Account)
def create_account(account_data: AccountCreate,
    db: Session = Depends(get_session),
    current_user: int = Depends(get_current_user)
):
    if account_data.account_type not in ACCOUNT_TYPES:
        raise HTTPException(
            status_code=400,
            detail=f"Type de compte invalide. Types autorisés : {ACCOUNT_TYPES}"
        )

    # Vérifier uniquement les comptes actifs du même type
    existing_active_account = db.query(models.Account).filter(
        models.Account.user_id == current_user,
        models.Account.type == account_data.account_type,
        models.Account.closed == False
    ).first()

    if existing_active_account:
        raise HTTPException(
            status_code=400,
            detail=f"Vous avez déjà un compte actif de type '{account_data.account_type}'"
        )

    new_account = models.Account(
        user_id=current_user,
        balance=0.0,
        main=False,
        closed=False,
        status=False,
        rib=generate_rib(current_user),
        date=datetime.utcnow(),
        type=account_data.account_type
    )
    db.add(new_account)
    db.commit()
    db.refresh(new_account)
    return new_account

@router.post("/close/{account_id}")
def close_account(account_id: int, db: Session = Depends(get_session), current_user: int = Depends(get_current_user)):
    """Clôturer un compte et transférer le solde vers le compte principal"""
    account = db.query(models.Account).filter(models.Account.id == account_id).first()
    if not account or account.user_id != current_user:
        raise HTTPException(status_code=400, detail="Compte introuvable ou non autorisé")
    if account.main:
        raise HTTPException(status_code=400, detail="Impossible de clôturer le compte principal")
    if account.closed:
        raise HTTPException(status_code=400, detail="Le compte est déjà fermé")
    if account.status:
        raise HTTPException(status_code=400, detail="Le compte a des transactions en cours")

    main_account = db.query(models.Account).filter(
        models.Account.user_id == current_user, models.Account.main == True
    ).first()
    if not main_account:
        raise HTTPException(status_code=400, detail="Compte principal introuvable")

    main_account.balance += account.balance
    account.closed = True
    db.commit()
    return {"detail": "Compte fermé", "main_account_balance": main_account.balance}

# ----------------- BENEFICIARIES -----------------
@router.post("/beneficiary/{account_id}", response_model=models.Beneficiary)
def add_beneficiary(account_id: int,data: BeneficiaryCreate, db: Session = Depends(get_session),current_user: int = Depends(get_current_user)):
    account = db.query(models.Account).filter(models.Account.id == account_id).first()
    rib = data.rib.replace(" ", "")
    name = data.name

    if not account or account.user_id != current_user:
        raise HTTPException(status_code=400, detail="Compte introuvable ou non autorisé")

    if account.rib == rib:
        raise HTTPException(status_code=400, detail="Impossible d'ajouter son propre RIB")

    # Vérifier si le même utilisateur a déjà ajouté ce RIB sur ce compte
    existing = db.query(models.Beneficiary).filter(
        models.Beneficiary.account_id == account_id,
        models.Beneficiary.rib == rib,
        models.Beneficiary.user_id == current_user
    ).first()

    if existing:
        raise HTTPException(status_code=400, detail="Vous avez déjà ajouté ce RIB")

    beneficiary = models.Beneficiary(
        account_id=account_id,
        name=name,
        rib=rib,
        user_id=current_user
    )
    db.add(beneficiary)
    db.commit()
    db.refresh(beneficiary)
    return beneficiary

@router.get("/beneficiary/{account_id}", response_model=list[models.Beneficiary])
def list_beneficiaries(account_id: int, db: Session = Depends(get_session), current_user: int = Depends(get_current_user)):
    account = db.query(models.Account).filter(models.Account.id == account_id).first()
    if not account or account.user_id != current_user:
        raise HTTPException(status_code=400, detail="Compte introuvable ou non autorisé")
    return db.query(models.Beneficiary).filter(models.Beneficiary.account_id == account_id).all()

@router.delete("/beneficiary/{account_id}/{rib}")
def delete_beneficiary(account_id: int, rib: str, db: Session = Depends(get_session), current_user: int = Depends(get_current_user)):
    account = db.query(models.Account).filter(models.Account.id == account_id).first()
    if not account or account.user_id != current_user:
        raise HTTPException(status_code=400, detail="Compte introuvable ou non autorisé")
    beneficiary = db.query(models.Beneficiary).filter(models.Beneficiary.account_id == account_id, models.Beneficiary.rib == rib).first()
    if not beneficiary:
        raise HTTPException(status_code=400, detail="Bénéficiaire introuvable")
    db.delete(beneficiary)
    db.commit()
    return {"detail": "Bénéficiaire supprimé"}

@router.get("/beneficiary/{account_id}/RIB", response_model=str)
def get_rib(account_id: int, db: Session = Depends(get_session), current_user: int = Depends(get_current_user)):
    account = db.query(models.Account).filter(models.Account.id == account_id).first()
    if not account or account.user_id != current_user:
        raise HTTPException(status_code=400, detail="Compte introuvable ou non autorisé")
    return account.rib


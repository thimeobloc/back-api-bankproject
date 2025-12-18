"""
Account-related API endpoints.

This module contains all routes related to bank accounts management,
including account creation, listing, closing accounts, and managing beneficiaries.
All endpoints require authentication using JWT tokens.
"""

from fastapi import APIRouter, HTTPException, Depends
from datetime import datetime, timezone
from sqlmodel import Session
from app.db import models
from app.db.database import get_session, init_db
from app.core.security import oauth2_scheme, SECRET_KEY, ALGORITHM
from jose import jwt, JWTError
import uuid
from app.schemas.account_schemas import *

router = APIRouter(prefix="/accounts", tags=["Accounts"])
init_db()

ACCOUNT_NOT_FOUND = "Compte introuvable ou non autorisé"


def get_current_user(token: str = Depends(oauth2_scheme)):
    """
    Retrieve the current authenticated user ID from the JWT token.

    Args:
        token (str): OAuth2 bearer token.

    Raises:
        HTTPException: If the token is invalid or does not contain a user ID.

    Returns:
        int: Authenticated user ID.
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: int = payload.get("user_id")
        if user_id is None:
            raise HTTPException(status_code=401, detail="Invalid token")
        return user_id
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")


def generate_rib(user_id: int) -> str:
    """
    Generate a unique RIB for a bank account.

    Args:
        user_id (int): Owner user ID.

    Returns:
        str: Generated RIB.
    """
    return f"FR{int(datetime.now(timezone.utc).timestamp())}{user_id}{uuid.uuid4().hex[:6]}"


@router.get("/", response_model=list[models.Account])
def list_accounts(
    current_user: int = Depends(get_current_user),
    db: Session = Depends(get_session)
):
    """
    Retrieve all accounts belonging to the authenticated user.

    Args:
        current_user (int): Authenticated user ID.
        db (Session): Database session.

    Returns:
        list[Account]: List of user accounts.
    """
    return db.query(models.Account).filter(models.Account.user_id == current_user).all()


@router.get("/myaccounts/", response_model=list[models.Account])
def view_accounts(
    db: Session = Depends(get_session),
    current_user: int = Depends(get_current_user)
):
    """
    Retrieve all active (non-closed) accounts of the authenticated user.

    Args:
        db (Session): Database session.
        current_user (int): Authenticated user ID.

    Returns:
        list[Account]: List of active accounts ordered by creation date.
    """
    accounts = db.query(models.Account).filter(
        models.Account.user_id == current_user,
        models.Account.closed == False
    ).order_by(models.Account.date.desc()).all()
    return accounts


@router.get("/{account_id}", response_model=models.Account)
def get_account(
    account_id: int,
    db: Session = Depends(get_session),
    current_user: int = Depends(get_current_user)
):
    """
    Retrieve a specific account by its ID.

    Args:
        account_id (int): Account identifier.
        db (Session): Database session.
        current_user (int): Authenticated user ID.

    Raises:
        HTTPException: If the account does not exist or does not belong to the user.

    Returns:
        Account: Account details.
    """
    account = db.query(models.Account).filter(
        models.Account.id == account_id,
        models.Account.user_id == current_user
    ).first()
    if not account:
        raise HTTPException(status_code=404, detail="Compte introuvable")
    return account


@router.post("/", response_model=models.Account)
def create_account(
    account_data: AccountCreate,
    db: Session = Depends(get_session),
    current_user: int = Depends(get_current_user)
):
    """
    Create a new bank account for the authenticated user.

    Args:
        account_data (AccountCreate): Account creation payload.
        db (Session): Database session.
        current_user (int): Authenticated user ID.

    Raises:
        HTTPException:
            - If the account type is invalid.
            - If an active account of the same type already exists.

    Returns:
        Account: Newly created account.
    """
    if account_data.account_type not in ACCOUNT_TYPES:
        raise HTTPException(
            status_code=400,
            detail=f"Type de compte invalide. Types autorisés : {ACCOUNT_TYPES}"
        )

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
        date=datetime.now(timezone.utc),
        type=account_data.account_type
    )
    db.add(new_account)
    db.commit()
    db.refresh(new_account)
    return new_account


@router.post("/close/{account_id}")
def close_account(
    account_id: int,
    db: Session = Depends(get_session),
    current_user: int = Depends(get_current_user)
):
    """
    Close a secondary bank account and transfer its balance to the main account.

    Args:
        account_id (int): Account identifier.
        db (Session): Database session.
        current_user (int): Authenticated user ID.

    Raises:
        HTTPException: If the account cannot be closed.

    Returns:
        dict: Closure confirmation and updated main account balance.
    """
    account = db.query(models.Account).filter(models.Account.id == account_id).first()
    if not account or account.user_id != current_user:
        raise HTTPException(status_code=400, detail=ACCOUNT_NOT_FOUND)
    if account.main:
        raise HTTPException(status_code=400, detail="Impossible de clôturer le compte principal")
    if account.closed:
        raise HTTPException(status_code=400, detail="Le compte est déjà fermé")
    if account.status:
        raise HTTPException(status_code=400, detail="Le compte a des transactions en cours")

    main_account = db.query(models.Account).filter(
        models.Account.user_id == current_user,
        models.Account.main == True
    ).first()
    if not main_account:
        raise HTTPException(status_code=400, detail="Compte principal introuvable")

    main_account.balance += account.balance
    account.closed = True
    db.commit()
    return {"detail": "Compte fermé", "main_account_balance": main_account.balance}


@router.post("/beneficiary/{account_id}", response_model=models.Beneficiary)
def add_beneficiary(
    account_id: int,
    data: BeneficiaryCreate,
    db: Session = Depends(get_session),
    current_user: int = Depends(get_current_user)
):
    """
    Add a beneficiary to a specific account.

    Args:
        account_id (int): Account identifier.
        data (BeneficiaryCreate): Beneficiary information.
        db (Session): Database session.
        current_user (int): Authenticated user ID.

    Raises:
        HTTPException: If the beneficiary cannot be added.

    Returns:
        Beneficiary: Created beneficiary.
    """
    account = db.query(models.Account).filter(models.Account.id == account_id).first()
    rib = data.rib.replace(" ", "")
    name = data.name

    if not account or account.user_id != current_user:
        raise HTTPException(status_code=400, detail=ACCOUNT_NOT_FOUND)

    if account.rib == rib:
        raise HTTPException(status_code=400, detail="Impossible d'ajouter son propre RIB")

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
def list_beneficiaries(
    account_id: int,
    db: Session = Depends(get_session),
    current_user: int = Depends(get_current_user)
):
    """
    Retrieve all beneficiaries associated with an account.

    Args:
        account_id (int): Account identifier.
        db (Session): Database session.
        current_user (int): Authenticated user ID.

    Returns:
        list[Beneficiary]: List of beneficiaries.
    """
    account = db.query(models.Account).filter(models.Account.id == account_id).first()
    if not account or account.user_id != current_user:
        raise HTTPException(status_code=400, detail=ACCOUNT_NOT_FOUND)
    return db.query(models.Beneficiary).filter(
        models.Beneficiary.account_id == account_id
    ).all()


@router.delete("/beneficiary/{account_id}/{rib}")
def delete_beneficiary(
    account_id: int,
    rib: str,
    db: Session = Depends(get_session),
    current_user: int = Depends(get_current_user)
):
    """
    Delete a beneficiary from an account.

    Args:
        account_id (int): Account identifier.
        rib (str): Beneficiary RIB.
        db (Session): Database session.
        current_user (int): Authenticated user ID.

    Raises:
        HTTPException: If the beneficiary does not exist.

    Returns:
        dict: Deletion confirmation message.
    """
    account = db.query(models.Account).filter(models.Account.id == account_id).first()
    if not account or account.user_id != current_user:
        raise HTTPException(status_code=400, detail=ACCOUNT_NOT_FOUND)

    beneficiary = db.query(models.Beneficiary).filter(
        models.Beneficiary.account_id == account_id,
        models.Beneficiary.rib == rib
    ).first()
    if not beneficiary:
        raise HTTPException(status_code=400, detail="Bénéficiaire introuvable")

    db.delete(beneficiary)
    db.commit()
    return {"detail": "Bénéficiaire supprimé"}


@router.get("/beneficiary/{account_id}/RIB", response_model=str)
def get_rib(
    account_id: int,
    db: Session = Depends(get_session),
    current_user: int = Depends(get_current_user)
):
    """
    Retrieve the RIB of a specific account.

    Args:
        account_id (int): Account identifier.
        db (Session): Database session.
        current_user (int): Authenticated user ID.

    Returns:
        str: Account RIB.
    """
    account = db.query(models.Account).filter(models.Account.id == account_id).first()
    if not account or account.user_id != current_user:
        raise HTTPException(status_code=400, detail=ACCOUNT_NOT_FOUND)
    return account.rib

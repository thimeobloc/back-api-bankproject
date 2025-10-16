from fastapi import APIRouter, HTTPException, Depends
from datetime import datetime
from app.db import models
from app.schemas.account_schemas import AccountCreate, AccountOut
from random import randint
from sqlmodel import Session, select
from app.db.database import get_session, init_db
import uuid

router = APIRouter(prefix="/accounts", tags=["Accounts"])

init_db()


def generate_rib(user_id: int) -> str:
    """Generate a random RIB for an account"""
    # Return the RIB as a string with FR76 and the banking institution's numbers
    return f"FR{int(datetime.utcnow().timestamp())}{user_id}{uuid.uuid4().hex[:6]}"


#<---------------- ACCOUNTS ---------------->
@router.get("/", response_model=list[models.Account])
def list_accounts_endpoint(db: Session = Depends(get_session)):
    """List all accounts"""
    # Return all accounts from the database
    return db.exec(select(models.Account)).all()


@router.post("/{user_id}/", response_model=models.Account)
def create_account_endpoint(user_id: int, db: Session = Depends(get_session)):
    """Create a new account for an existing user"""
    # Look for the user with his id
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=400, detail="L'utilisateur n'existe pas")

    # Look for the main account of the user
    main_account = db.query(models.Account).filter(
        models.Account.user_id == user_id,
        models.Account.main == True
    ).first()
    if not main_account:
        raise HTTPException(status_code=404, detail="Compte principal introuvable")

    # Create a new secondary account
    new_account = models.Account(
        user_id=user_id,
        balance=0.0,
        main=False,
        closed=False,
        status=False,
        rib=generate_rib(user_id),
        date=datetime.utcnow()
    )

    db.add(new_account)
    db.commit()
    db.refresh(new_account)

    return new_account


@router.get("/account/{user_id}/", response_model=list[models.Account])
def view_accounts(user_id: int, db: Session = Depends(get_session)):
    """View all accounts of a user that are not closed"""
    # Look for the user with his id
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=400, detail="L'utilisateur n'existe pas")

    # Browse the list of accounts
    accounts = db.query(models.Account).filter(
        models.Account.user_id == user_id,
        models.Account.closed == False
    ).order_by(models.Account.date.desc()).all()

    # Return the accounts sorted by descending date
    return accounts


@router.post("/closed/{account_id}/{user_id}")
def close_account(account_id: int, user_id: int, db: Session = Depends(get_session)):
    """Close an account of a user"""
    # Look for the account with his id
    account = db.query(models.Account).filter(models.Account.id == account_id).first()
    # Look for the user with his id
    user = db.query(models.User).filter(models.User.id == user_id).first()

    # If there's no account return an error message
    if not account:
        raise HTTPException(status_code=400, detail="Le compte n'existe pas")
        
    # If there's no user return an error message
    if not user:
        raise HTTPException(status_code=400, detail="L'utilisateur n'existe pas")
        
    # Check if the account is closed
    if account.closed:
        raise HTTPException(status_code=400, detail="Le compte n'existe plus")
        
    # Check if the account is the main account
    if account.main:
        raise HTTPException(status_code=400, detail="Vous ne pouvez pas clôturer votre compte principal")
        
    # Check if the account belongs to the user
    if account.user_id != user_id:
        raise HTTPException(status_code=400, detail="Ce n'est pas votre compte monsieur")
        
    # Check if the account has ongoing transactions
    if account.status:
        raise HTTPException(status_code=400, detail="Le compte a des transactions en cours")
    
    # Close the account
    account.closed = True

    # Look for the main account of the user
    main_account = db.query(models.Account).filter(
        models.Account.user_id == user_id,
        models.Account.main == True
    ).first()
    if not main_account:
        raise HTTPException(status_code=400, detail="Il n'y a pas de compte principal :(")
        
    # Transfer the balance to the main account
    main_account.balance += account.balance

    db.commit()
    return {"detail": "Votre compte a été fermé", "main_account_balance":main_account.balance}


#<---------------- BENEFICIARIES ---------------->
@router.post("/beneficiary/{account_id}/{rib}/{name}/{user_id}", response_model=models.Beneficiary)
def add_beneficiary(account_id: int, rib: str, name: str, user_id: int, db: Session = Depends(get_session)):
    """Add a beneficiary to an account"""
    # Look for the account with his id
    account = db.query(models.Account).filter(models.Account.id == account_id).first()
    # Look for the user with his id
    user = db.query(models.User).filter(models.User.id == user_id).first()

    # If there's no user return an error message
    if not user:
        raise HTTPException(status_code=400, detail="L'utilisateur n'existe pas")
        
    # If there's no account return an error message
    if not account:
        raise HTTPException(status_code=400, detail="Le compte n'existe pas")
        
    # Check if the account belongs to the user
    if account.user_id != user_id:
        raise HTTPException(status_code=400, detail="Ce n'est pas votre compte monsieur")
        
    # Check if the account is closed
    if account.closed:
        raise HTTPException(status_code=400, detail="Le compte n'existe plus")
        
    # Check if the RIB is the same as the account's RIB
    if account.rib == rib:
        raise HTTPException(status_code=400, detail="Vous ne pouvez pas ajouter votre propre RIB comme bénéficiaire")
        
    # Vérifie si le bénéficiaire existe déjà
    existing_beneficiary = db.query(models.Beneficiary).filter(
        models.Beneficiary.account_id == account_id,
        models.Beneficiary.rib == rib
    ).first()

    # If the beneficiary already exists return an error message
    if existing_beneficiary:
        raise HTTPException(status_code=400, detail="Ce bénéficiaire existe déjà")
        
    # Création du bénéficiaire
    beneficiary = models.Beneficiary(
        account_id=account_id,
        name=name,
        rib=rib,
    )
    db.add(beneficiary)
    db.commit()
    db.refresh(beneficiary)
        
    return beneficiary


@router.get("/beneficiary/{account_id}/{user_id}", response_model=list[models.Beneficiary])
def list_beneficiaries(account_id: int, user_id: int, db: Session = Depends(get_session)):
    """List all beneficiaries of an account"""
    # Look for the account with his id
    account = db.query(models.Account).filter(models.Account.id == account_id).first()
    # Look for the user with his id
    user = db.query(models.User).filter(models.User.id == user_id).first()

    # If there's no user return an error message
    if not user:
        raise HTTPException(status_code=400, detail="L'utilisateur n'existe pas")
        
    # If there's no account return an error message
    if not account:
        raise HTTPException(status_code=400, detail="Le compte n'existe pas")
        
    # Check if the account belongs to the user
    if account.user_id != user_id:
        raise HTTPException(status_code=400, detail="Ce n'est pas votre compte monsieur")
        
    # Return the list of beneficiaries
    return db.query(models.Beneficiary).filter(models.Beneficiary.account_id == account_id).all()


@router.get("/beneficiary/user/{user_id}/{account_id}/RIB", response_model=str)
def get_rib(user_id: int, account_id: int, db: Session = Depends(get_session)):
    """Get the RIB of an account"""
    # Look for the user with his id
    user = db.query(models.User).filter(models.User.id == user_id).first()
    # Look for the account with his id
    account = db.query(models.Account).filter(models.Account.id == account_id).first()

    # If there's no user return an error message
    if not user:
        raise HTTPException(status_code=400, detail="L'utilisateur n'existe pas")
        
    # If there's no account return an error message
    if not account:
        raise HTTPException(status_code=400, detail="Le compte n'existe pas")
        
    # Check if the account belongs to the user
    if account.user_id != user_id:
        raise HTTPException(status_code=400, detail="Ce n'est pas votre compte monsieur")
        
    # Check if the account is closed
    if account.closed:
        raise HTTPException(status_code=400, detail="Le compte n'existe plus")
        
    # Return the RIB
    return account.rib


@router.delete("/beneficiary/{account_id}/{rib}/{user_id}")
def delete_beneficiary(account_id: int, rib: str, user_id: int, db: Session = Depends(get_session)):
    """Delete a beneficiary from an account"""
    # Look for the account with his id
    account = db.query(models.Account).filter(models.Account.id == account_id).first()
    # Look for the user with his id
    user = db.query(models.User).filter(models.User.id == user_id).first()

    # If there's no user return an error message
    if not user:
        raise HTTPException(status_code=400, detail="L'utilisateur n'existe pas")
        
    # If there's no account return an error message
    if not account:
        raise HTTPException(status_code=400, detail="Le compte n'existe pas")
        
    # Check if the account belongs to the user
    if account.user_id != user_id:
        raise HTTPException(status_code=400, detail="Ce n'est pas votre compte monsieur")
        
    # Look for the beneficiary with his rib
    beneficiary = db.query(models.Beneficiary).filter(
        models.Beneficiary.account_id == account_id,
        models.Beneficiary.rib == rib
    ).first()

    # If there's no beneficiary return an error message
    if not beneficiary:
        raise HTTPException(status_code=400, detail="Le bénéficiaire n'existe pas")
        
    # Remove the beneficiary from the account's list
    db.delete(beneficiary)
    db.commit()
    return {"detail": "Le bénéficiaire a été supprimé"}

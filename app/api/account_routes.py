from fastapi import APIRouter, HTTPException, Depends
from datetime import datetime
from app.db import models
from app.schemas.account_schemas import AccountCreate, AccountOut
from random import randint
from sqlmodel import Session
from app.db.database import users_db, accounts_db, engine, init_db, get_session

router = APIRouter(prefix="/accounts", tags=["Accounts"])

init_db()

def generate_rib():
    """Generate a random RIB for an account"""
    a = [str(randint(0, 9)) for _ in range(18)] # Generate a list of 18 numbers between 0 and 9
    return "FR7627127" + "".join(a) # Return the RIB as a string with FR76 and the banking institution's numbers


#<---------------- ACCOUNTS ---------------->
@router.get("/", response_model=list[models.Account])
def list_accounts_endpoint():
    """List all accounts"""
    return accounts_db


@router.post("/{user_id}/", response_model=models.Account)
def create_account_endpoint(user_id : int, db: get_session = Depends(get_session), users_db = Depends(users_db), accounts_db = Depends(accounts_db)):
    """Create a new account for an existing user"""
    user = next((use for use in users_db if use.id == user_id), None) #Look for the user with his id

    #If there's no user return an error message
    if not user:
        raise HTTPException(status_code=400, detail="L'utilisateur' n'existe pas")
        
    main_account = next((acc for acc in accounts_db if acc.user_id == user_id), None) # Look for the main account of the user

    #If there's no main account return an error message
    if not main_account:
        raise HTTPException(status_code=404, detail="Account not found")

    account_id = len(accounts_db) + 1 # ID auto-incremented => Take the last one of the account's list and add 1

    #transfor account object to dictionary
    account = models.Account(
    user_id=main_account.user_id,
    balance=0.0,
    main=False,
    closed=False,
    status=False,
    rib=f"FR{int(datetime.utcnow().timestamp())}{account.id}", # Generate RIB
    date=datetime.utcnow()
    )
    db_account = account
    db.add(db_account)
    db.commit()
    db.refresh(db_account)

    return account

@router.get("/account/{user_id}/", response_model=list[models.Account])
def view_accounts(user_id: int, users_db = Depends(users_db), accounts_db = Depends(accounts_db)):
    """View all accounts of a user that are not closed"""
    user = next((use for use in users_db if use.id == user_id), None)  # Look for the user with his id

    # If there's no user return an error message
    if not user:
        raise HTTPException(status_code=400, detail="L'utilisateur' n'existe pas")
        
    accounts = []

    # Browse the list of accounts
    for acc in accounts_db:
        if user_id == acc.user_id:  # If the account is one of the user's accounts
            if not acc.closed:     # Look if the account is not closed
                # Convert the date to datetime if it's stored as string
                if isinstance(acc.date, str):
                    acc.date = datetime.fromisoformat(acc.date)
                accounts.append(acc)   # Add it to the list

    # Sort the list by descending date
    creations_sorted = sorted(accounts, key=lambda x: x.date, reverse=True)

    return creations_sorted


@router.post("/closed/{account_id}/{user_id}")
def close_account(account_id: int, user_id: int, users_db = Depends(users_db), accounts_db = Depends(accounts_db)):
    """Close an account of a user"""

    account = next((acc for acc in accounts_db if acc.id == account_id), None) #Look for the account with his id
    user = next((use for use in users_db if use.id == user_id), None) #Look for the user with his id

    #If there's no account return an error message
    if not account:
        raise HTTPException(status_code=400, detail="Le compte n\'existe pas")
        
    #If there's no user return an error message
    if not user:
        raise HTTPException(status_code=400, detail="L\'utilisateur n\'existe pas")
        
    #Check if the account is closed
    if account.closed:
        raise HTTPException(status_code=400, detail="Le compte n\'existe plus")
        
    #Check if the account is the main account
    if account.main:
        raise HTTPException(status_code=400, detail="Vous ne pouvez pas clôturer votre compte principal")
        
    #Check if the account belongs to the user
    if account.user_id != user_id:
        raise HTTPException(status_code=400, detail="Ce n\'est pas votre compte monsieur")
        
    #Check if the account has ongoing transactions
    if account.status:
        raise HTTPException(status_code=400, detail="Le compte a des transactions en cours")
    else:
        account.closed = True #Close the account
        main_account = next((acc for acc in accounts_db if acc["user_id"] == user_id and acc["main"]==True), None) #Look for the main account of the user

        #If there's no main account return an error message
        if not main_account:
            raise HTTPException(status_code=400, detail="Il n'y a pas de compte principal :(")
            
        main_account.balance +=account.balance #Transfer the balance to the main account
    return{"Votre compte a été fermé"}




#<---------------- BENEFICIARIES ---------------->
@router.post("/beneficiary/{account_id}/{rib}/{name}/{user_id}", response_model=models.Beneficiary)
def add_beneficiary(benef: models.Beneficiary, rib: str,  account_id: int, name:str, user_id: int, users_db = Depends(users_db), accounts_db = Depends(accounts_db), db: Session = Depends(get_session)):
    """Add a beneficiary to an account"""
    account = next((acc for acc in accounts_db if acc.id == account_id), None) #Look for the account with his id
    user = next((use for use in users_db if use.id == user_id), None) #Look for the user with his id

    #If there's no user return an error message
    if not user:
        raise HTTPException(status_code=400, detail="L'utilisateur n'existe pas")
        
    #If there's no account return an error message
    if not account:
        raise HTTPException(status_code=400, detail="Le compte n'existe pas")
        
    #Check if the account belongs to the user
    if account.user_id != user_id:
        raise HTTPException(status_code=400, detail="Ce n\'est pas votre compte monsieur")
        
    #Check if the account is closed
    if account.closed:
        raise HTTPException(status_code=400, detail="Le compte n'existe plus")
        
    #Check if the RIB is the same as the account's RIB
    if account.rib == rib:
        raise HTTPException(status_code=400, detail="Vous ne pouvez pas ajouter votre propre RIB comme bénéficiaire")
        
    # Vérifie si le bénéficiaire existe déjà
    existing_beneficiary = next((b for b in account.beneficiary if b.rib == rib), None)

    #If the beneficiary already exists return an error message
    if existing_beneficiary:
        raise HTTPException(status_code=400, detail="Ce bénéficiaire existe déjà")
        
    # Création du bénéficiaire
    beneficiary = models.Beneficiary(
    account_id=account_id,
    name=name,
    rib=rib,
    )
    db_beneficiary = beneficiary
    db.add(db_beneficiary)
    db.commit()
    db.refresh(db_beneficiary)
    account.beneficary = beneficiary
        
    return db_beneficiary


@router.get("/beneficiary/{account_id}/{user_id}", response_model=list[models.Beneficiary])
def list_beneficiaries(account_id: int, user_id: int, users_db = Depends(users_db), accounts_db = Depends(accounts_db)):
    """List all beneficiaries of an account"""
    account = next((acc for acc in accounts_db if acc.id == account_id), None) #Look for the account with his id
    user = next((use for use in users_db if use.id == user_id), None) #Look for the user with his id

    #If there's no user return an error message
    if not user:
        raise HTTPException(status_code=400, detail="L'utilisateur n'existe pas")
        
    #If there's no account return an error message
    if not account:
        raise HTTPException(status_code=400, detail="Le compte n\'existe pas")
        
    #Check if the account belongs to the user
    if account.user_id != user_id:
        raise HTTPException(status_code=400, detail="Ce n\'est pas votre compte monsieur")
        
    return account.beneficiary


@router.get("/beneficiary/{user_id}/{account_id}/RIB", response_model= str)
def get_rib(user_id: int, account_id: int, users_db = Depends(users_db), accounts_db = Depends(accounts_db)):
    """Get the RIB of an account"""
    user = next((use for use in users_db if use.id == user_id), None) #Look for the user with his id
    account = next((acc for acc in accounts_db if acc.id == account_id), None) #Look for the account with his id

    #If there's no user return an error message
    if not user:
        raise HTTPException(status_code=400, detail="L'utilisateur n'existe pas")
        
    #If there's no account return an error message
    if not account:
        raise HTTPException(status_code=400, detail="Le compte n'existe pas")
        
    #Check if the account belongs to the user
    if account.user_id != user_id:
        raise HTTPException(status_code=400, detail="Ce n'est pas votre compte monsieur")
        
    #Check if the account is closed
    if account.closed:
        raise HTTPException(status_code=400, detail="Le compte n'existe plus")
        
    return account.rib


@router.delete("/beneficiary/{account_id}/{rib}/{user_id}")
def delete_beneficiary(account_id: int, rib: str, user_id: int, users_db = Depends(users_db), accounts_db = Depends(accounts_db)):
    """Delete a beneficiary from an account"""
    account = next((acc for acc in accounts_db if acc.id == account_id), None) #Look for the account with his id
    user = next((use for use in users_db if use.id == user_id), None) #Look for the user with his id

    #If there's no user return an error message
    if not user:
        raise HTTPException(status_code=400, detail="L'utilisateur n'existe pas")
        
    #If there's no account return an error message
    if not account:
        raise HTTPException(status_code=400, detail="Le compte n\'existe pas")
        
    #Check if the account belongs to the user
    if account.user_id != user_id:
        raise HTTPException(status_code=400, detail="Ce n\'est pas votre compte monsieur")
        
    beneficiary = next((b for b in account["beneficiary"] if b["rib"] == rib), None)# Look for the beneficiary with his rib

    #If there's no beneficiary return an error message
    if not beneficiary:
        raise HTTPException(status_code=400, detail="Le bénéficiaire n\'existe pas")
        

    account.beneficiary.remove(beneficiary) #Remove the beneficiary from the account's list
    return {"Le bénéficiaire a été supprimé"}


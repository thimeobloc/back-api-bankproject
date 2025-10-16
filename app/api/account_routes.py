from fastapi import APIRouter, HTTPException
from app.schemas.account_schemas import*
from app.db.database import accounts_db, users_db
from datetime import datetime
from random import randint

router = APIRouter(prefix="/accounts", tags=["Accounts"])


def generate_rib():
    """Generate a random RIB for an account"""
    a=[str(randint(0, 9)) for _ in range(18)] # Generate a list of 18 numbers between 0 and 9
    return "FR7627127"+a # Return the RIB as a string with FR76 and the banking institution's numbers


#<---------------- ACCOUNTS ---------------->
@router.get("/", response_model=list[AccountCreate])
def list_accounts_endpoint():
    """List all accounts"""
    return accounts_db


@router.post("/", response_model=AccountOut)
def create_account_endpoint(account: AccountCreate):
    """Create a new account for an existing user"""
    user = next((use for use in users_db if use["id"] == account.user_id), None) #Look for the user with his id

    #If there's no user return an error message
    if not user:
        raise HTTPException(status_code=400, detail="L'utilisateur' n'existe pas")
    
    main_account = next((acc for acc in accounts_db if acc["user_id"] == account.user_id), None) # Look for the main account of the user

    #If there's no main account return an error message
    if not main_account:
        raise HTTPException(status_code=404, detail="Account not found")

    account_id = len(accounts_db) + 1 # ID auto-incremented => Take the last one of the account's list and add 1

    account_dict = account.dict()  #transfor account object to dictionary
    account_dict["id"] = account_id
    account_dict["balance"] = 0.0
    account_dict["main"] = False
    account_dict["user_id"] = main_account["user_id"]
    account_dict["closed"] = False
    account_dict["status"] = False
    account_dict["date"] = account.date or datetime.now().isoformat() #Add the current date if no date is provided
    account_dict["rib"] = generate_rib()  #Generate a RIB for the account

    accounts_db.append(account_dict) #add the account to the account's list

    return account_dict


@router.get("/account/{user_id}/", response_model=list[AccountOut])
def view_accounts(user_id: int):
    """View all accounts of a user that are not closed"""
    user = next((use for use in users_db if use["id"] == user_id), None) #Look for the user with his id

    #If there's no user return an error message
    if not user:
        raise HTTPException(status_code=400, detail="L'utilisateur' n'existe pas")
    
    accounts=[]

    #Brow the list of accounts
    for acc in accounts_db:
        if user_id == acc["user_id"]: #If the account is one of the user's accounts
            if not acc["closed"]: #Look if the account is not closed
                accounts.append(acc) #Add it to the list

    creations_sorted = sorted(accounts, key=lambda x: x["date"], reverse=True) #Sort the list by descending date

    return creations_sorted


@router.post("/closed/{account_id}/{user_id}")
def close_account(account_id: int, user_id: int):
    """Close an account of a user"""

    account = next((acc for acc in accounts_db if acc["id"] == account_id), None) #Look for the account with his id
    user = next((use for use in users_db if use["id"] == user_id), None) #Look for the user with his id

    #If there's no account return an error message
    if not account:
        raise HTTPException(status_code=400, detail="Le compte n\'existe pas")
    
    #If there's no user return an error message
    if not user:
        raise HTTPException(status_code=400, detail="L\'utilisateur n\'existe pas")
    
    #Check if the account is closed
    if account["closed"]:
        raise HTTPException(status_code=400, detail="Le compte n\'existe plus")
    
    #Check if the account is the main account
    if account["main"]:
        raise HTTPException(status_code=400, detail="Vous ne pouvez pas clôturer votre compte principal")
    
    #Check if the account belongs to the user
    if account["user_id"] != user_id:
        raise HTTPException(status_code=400, detail="Ce n\'est pas votre compte monsieur")
    
    #Check if the account has ongoing transactions
    if account["status"]:
        raise HTTPException(status_code=400, detail="Le compte a des transactions en cours")
    else:
        account["closed"] = True #Close the account
        main_account = next((acc for acc in accounts_db if acc["user_id"] == user_id and acc["main"]==True), None) #Look for the main account of the user

        #If there's no main account return an error message
        if not main_account:
            raise HTTPException(status_code=400, detail="Il n'y a pas de compte principal :(")
        
        main_account["balance"] +=account["balance"]#Transfer the balance to the main account
    return{"Votre compte a été fermé"}




#<---------------- BENEFICIARIES ---------------->
@router.post("/beneficiary/{account_id}/{rib}/{name}/{user_id}", response_model=beneficiary)
def add_beneficiary(benef: beneficiary, rib: str, account_id: int, name:str, user_id: int):
    """Add a beneficiary to an account"""
    account = next((acc for acc in accounts_db if acc["id"] == account_id), None) #Look for the account with his id
    user = next((use for use in users_db if use["id"] == user_id), None) #Look for the user with his id

    #If there's no user return an error message
    if not user:
        raise HTTPException(status_code=400, detail="L'utilisateur n'existe pas")
    
    #If there's no account return an error message
    if not account:
        raise HTTPException(status_code=400, detail="Le compte n'existe pas")
    
    #Check if the account belongs to the user
    if account["user_id"] != user_id:
        raise HTTPException(status_code=400, detail="Ce n\'est pas votre compte monsieur")
    
    #Check if the account is closed
    if account["closed"]:
        raise HTTPException(status_code=400, detail="Le compte n'existe plus")
    
    #Check if the RIB is the same as the account's RIB
    if account["rib"] == rib:
        raise HTTPException(status_code=400, detail="Vous ne pouvez pas ajouter votre propre RIB comme bénéficiaire")
    
    # Vérifie si le bénéficiaire existe déjà
    existing_beneficiary = next((b for b in account["beneficiary"] if b["rib"] == rib), None)

    #If the beneficiary already exists return an error message
    if existing_beneficiary:
        raise HTTPException(status_code=400, detail="Ce bénéficiaire existe déjà")
    
    # Création du bénéficiaire
    benef_dict = benef.dict() #transfor beneficiary object to dictionary
    benef_dict["account_id"] = account_id
    benef_dict["name"] = name
    benef_dict["rib"] = rib
    benef_dict["date"] = benef.date or datetime.now().isoformat() #Add the current date if no date is provided

    account["beneficiary"].append(benef_dict) #add the beneficiary to the account's list
    return benef_dict


@router.get("/beneficiary/{account_id}/{user_id}", response_model=list[beneficiary])
def list_beneficiaries(account_id: int, user_id: int):
    """List all beneficiaries of an account"""
    account = next((acc for acc in accounts_db if acc["id"] == account_id), None) #Look for the account with his id
    user = next((use for use in users_db if use["id"] == user_id), None) #Look for the user with his id

    #If there's no user return an error message
    if not user:
        raise HTTPException(status_code=400, detail="L'utilisateur n'existe pas")
    
    #If there's no account return an error message
    if not account:
        raise HTTPException(status_code=400, detail="Le compte n\'existe pas")
    
    #Check if the account belongs to the user
    if account["user_id"] != user_id:
        raise HTTPException(status_code=400, detail="Ce n\'est pas votre compte monsieur")
    
    return account["beneficiary"]


@router.get("/beneficiary/{user_id}/{account_id}/RIB", response_model= str)
def get_rib(user_id: int, account_id: int):
    """Get the RIB of an account"""
    user = next((use for use in users_db if use["id"] == user_id), None) #Look for the user with his id
    account = next((acc for acc in accounts_db if acc["id"] == account_id), None) #Look for the account with his id

    #If there's no user return an error message
    if not user:
        raise HTTPException(status_code=400, detail="L'utilisateur n'existe pas")
    
    #If there's no account return an error message
    if not account:
        raise HTTPException(status_code=400, detail="Le compte n'existe pas")
    
    #Check if the account belongs to the user
    if account["user_id"] != user_id:
        raise HTTPException(status_code=400, detail="Ce n'est pas votre compte monsieur")
    
    #Check if the account is closed
    if account["closed"]:
        raise HTTPException(status_code=400, detail="Le compte n'existe plus")
    
    return account["rib"]


@router.delete("/beneficiary/{account_id}/{rib}/{user_id}")
def delete_beneficiary(account_id: int, rib: str, user_id: int):
    """Delete a beneficiary from an account"""
    account = next((acc for acc in accounts_db if acc["id"] == account_id), None) #Look for the account with his id
    user = next((use for use in users_db if use["id"] == user_id), None) #Look for the user with his id

    #If there's no user return an error message
    if not user:
        raise HTTPException(status_code=400, detail="L'utilisateur n'existe pas")
    
    #If there's no account return an error message
    if not account:
        raise HTTPException(status_code=400, detail="Le compte n\'existe pas")
    
    #Check if the account belongs to the user
    if account["user_id"] != user_id:
        raise HTTPException(status_code=400, detail="Ce n\'est pas votre compte monsieur")
    
    beneficiary = next((b for b in account["beneficiary"] if b["rib"] == rib), None)# Look for the beneficiary with his rib

    #If there's no beneficiary return an error message
    if not beneficiary:
        raise HTTPException(status_code=400, detail="Le bénéficiaire n\'existe pas")
    

    account["beneficiary"].remove(beneficiary) #Remove the beneficiary from the account's list
    return {"Le bénéficiaire a été supprimé"}


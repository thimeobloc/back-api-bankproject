from fastapi import APIRouter, HTTPException
from app.schemas.account_schemas import*
from app.db.database import accounts_db, users_db
from datetime import datetime
from random import randint

router = APIRouter(prefix="/accounts", tags=["Accounts"])


def generate_rib():
    return "FR76".join([str(randint(0, 9)) for _ in range(23)])

@router.get("/", response_model=list[AccountCreate])
def list_accounts_endpoint():
    return accounts_db

@router.post("/", response_model=AccountOut)
def create_account_endpoint(account: AccountCreate):
    main_account = next((acc for acc in accounts_db if acc["user_id"] == account.user_id), None)
    if not main_account:
        raise HTTPException(status_code=404, detail="Account not found")

    account_id = len(accounts_db) + 1

    account_dict = account.dict()
    account_dict["id"] = account_id
    account_dict["balance"] = 0.0
    account_dict["main"] = False
    account_dict["user_id"] = main_account["user_id"]
    account_dict["closed"] = False
    account_dict["status"] = False
    account_dict["date"] = account.date or datetime.now().isoformat()
    account_dict["rib"] = generate_rib()  

    accounts_db.append(account_dict)

    return account_dict


@router.get("/account/{user_id}/", response_model=list[AccountOut])
def view_accounts(user_id: int):
    user = next((use for use in users_db if use["id"] == user_id), None)
    if not user:
        raise HTTPException(status_code=400, detail="L'utilisateur' n'existe pas")
    accounts=[]
    for acc in accounts_db:
        if user_id == acc["user_id"]:
            if not acc["closed"]:
                accounts.append(acc)
    creations_sorted = sorted(accounts, key=lambda x: x["date"], reverse=True)

    return creations_sorted


@router.post("/closed/{account_id}/{user_id}")
def close_account(account_id: int, user_id: int):
    account = next((acc for acc in accounts_db if acc["id"] == account_id), None)
    user = next((use for use in users_db if use["id"] == user_id), None)
    if not account:
        raise HTTPException(status_code=400, detail="Le compte n\'existe pas")
    if not user:
        raise HTTPException(status_code=400, detail="L\'utilisateur n\'existe pas")
    if account["closed"]:
        raise HTTPException(status_code=400, detail="Le compte n\'existe plus")
    if account["main"]:
        raise HTTPException(status_code=400, detail="Vous ne pouvez pas clôturer votre compte principal")
    if account["user_id"] != user_id:
        raise HTTPException(status_code=400, detail="Ce n\'est pas votre compte monsieur")
    if account["status"]:
        raise HTTPException(status_code=400, detail="Le compte a des transactions en cours")
    else:
        account["closed"] = True
        main_account = next((acc for acc in accounts_db if acc["user_id"] == user_id and acc["main"]==True), None)
        if not main_account:
            raise HTTPException(status_code=400, detail="Il n'y a pas de compte principal :(")
        main_account["balance"] +=account["balance"]
    return{"Votre compte a été fermé"}

@router.post("/beneficiary/{account_id}/{rib}/{name}", response_model=beneficiary)
def add_beneficiary(benef: beneficiary, rib: str, account_id: int, name:str):
    #Mettre toutes les recherches
    account = next((acc for acc in accounts_db if acc["id"] == account_id), None)
    existing_beneficiary = next((b for b in account["beneficiary"] if b["rib"] == rib), None)

    #Vérifications
    if not account:
        raise HTTPException(status_code=400, detail="Le compte n\'existe pas")
    if account["closed"]:
        raise HTTPException(status_code=400, detail="Le compte n\'existe plus")
    if account["rib"] == rib:
        raise HTTPException(status_code=400, detail="Vous ne pouvez pas ajouter votre propre RIB comme bénéficiaire")
    if existing_beneficiary:
        raise HTTPException(status_code=400, detail="Ce bénéficiaire existe déjà")
    
    
    if existing_beneficiary["user_id"] == account["user_id"]:
        raise HTTPException(status_code=400, detail="Vous ne pouvez pas ajouter un bénéficiaire qui vous appartient")
    
    
    #Ajout
    benef_dict = benef.dict()
    benef_dict["account_id"] = existing_beneficiary["id"]
    benef_dict["name"] = name
    benef_dict["rib"] = rib
    benef_dict["date"] = benef.date or datetime.now().isoformat()
    
    for benef in account["beneficiary"]:
        if benef["rib"] == rib:
            raise HTTPException(status_code=400, detail="Le bénéficiaire existe déjà")
        if benef["name"] == name:
            raise HTTPException(status_code=400, detail="Le nom du bénéficiaire existe déjà")
    
    account["beneficiary"].append(benef_dict)



    return benef_dict

@router.get("/beneficiary/{account_id}", response_model=list[beneficiary])
def list_beneficiaries(account_id: int):
    account = next((acc for acc in accounts_db if acc["id"] == account_id), None)
    if not account:
        raise HTTPException(status_code=400, detail="Le compte n\'existe pas")
    
    return account["beneficiary"]
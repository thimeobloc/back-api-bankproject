from fastapi import FastAPI
from app.api.router import router as api_router
from app.db.database import users_db, accounts_db, balances_db

app = FastAPI(title="Bank API")

app.include_router(api_router)

@app.get("/")
def read_db():
    deposits = []
    withdraws = []
    transfers = []
    for account in accounts_db:
        deposits.append(account["deposit"]) #Dépot d'argent
        withdraws.append(account["withdraw"]) #Retrait d'argent
        transfers.append(account["transfer"]) #Transfer d'argent
    return {
        "users": users_db,
        "accounts": accounts_db,
        "balances":balances_db,
        "deposits": deposits,
        "withdraws": withdraws,
        "transfers": transfers
    }


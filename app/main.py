from fastapi import FastAPI
from app.api.router import router as api_router
from app.db.database import users_db, accounts_db

app = FastAPI(title="Bank API")

app.include_router(api_router)

@app.get("/")
def read_db():
    deposits = []
    withdraws = []
    transfers = []
    for account in accounts_db:
        deposits.append(account["deposit"])
        withdraws.append(account["withdraw"])
        transfers.append(account["transfer"])
    return {
        "users": users_db,
        "accounts": accounts_db,
        "deposits": deposits,
        "withdraws": withdraws,
        "transfers": transfers
    }

app = FastAPI()

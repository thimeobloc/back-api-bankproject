from fastapi import FastAPI
from app.api.router import router as api_router
from app.db.database import engine, init_db

# Import models pour créer les tables
from app.db import models

app = FastAPI(title="Bank API")

init_db()

app.include_router(api_router)

@app.get("/")
def root():
    return {"message": "Bank API is running"}

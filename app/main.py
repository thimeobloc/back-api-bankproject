from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.router import router as api_router
from app.db.database import engine, init_db

# Import models pour créer les tables
from app.db import models

app = FastAPI(title="Bank API")

init_db()

# ----------------- CORS -----------------
origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173"
]


app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,  # autorise seulement ton frontend
    allow_credentials=True,
    allow_methods=["*"],  # autorise GET, POST, PUT, DELETE...
    allow_headers=["*"],  # autorise tous les headers

# ----------------------------------------

app.include_router(api_router)

@app.get("/")
def root()
    return {"message": "Bank API is running"}

from fastapi import FastAPI
from app.api import user_routes

app = FastAPI(title="Bank API")

app.include_router(user_routes.router)

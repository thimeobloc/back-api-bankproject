from fastapi import FastAPI
from app.api import user_routes, auth_routes

app = FastAPI(title="Bank API")

app.include_router(user_routes.router)

app = FastAPI()

app.include_router(user_routes.router)
app.include_router(auth_routes.router)
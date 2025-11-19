from fastapi import APIRouter
from app.api import user_routes, account_routes, balance_routes

router = APIRouter()

router.include_router(user_routes.router)
router.include_router(account_routes.router)
router.include_router(balance_routes.router)

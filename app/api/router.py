"""
Main API router.

This module aggregates and registers all application route groups,
including user management, account management, and balance operations.
It serves as the central entry point for API routing.
"""

from fastapi import APIRouter
from app.api import user_routes, account_routes, balance_routes

router = APIRouter()

router.include_router(user_routes.router)
"""
Include all user-related endpoints.

Routes:
    - User registration
    - Authentication
    - User retrieval
"""

router.include_router(account_routes.router)
"""
Include all account-related endpoints.

Routes:
    - Account creation and closure
    - Account listing and details
    - Beneficiary management
"""

router.include_router(balance_routes.router)
"""
Include all balance-related endpoints.

Routes:
    - Deposits and withdrawals
    - Transfers between accounts
    - Transfer history and cancellation
"""

"""
Database configuration and session utilities.

This module configures the SQLModel database engines, provides session
dependencies for FastAPI, initializes database schemas, and exposes
helper functions to retrieve database entities.
"""

from sqlmodel import SQLModel, create_engine, Session, select
from app.db.models import User, Account, Deposit, Withdraw, Transfer
from fastapi import Depends
from sqlalchemy.pool import StaticPool

DATABASE_URL = "sqlite:///database.db"
"""
Main database connection URL.
"""

engine = create_engine(DATABASE_URL, echo=True)
"""
Primary SQLModel engine for the production database.
"""

TEST_DATABASE_URL = "sqlite:///:memory:"
"""
In-memory SQLite database URL used for testing.
"""

test_engine = create_engine(
    TEST_DATABASE_URL,
    echo=True,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool
)
"""
SQLModel engine configured for test execution.

Uses a static pool to allow multiple connections to the same
in-memory database.
"""

# ---------------------------
# Session dependencies
# ---------------------------
def get_session():
    """
    Provide a database session dependency.

    This function is used by FastAPI to inject a database session
    into request handlers.

    Yields:
        Session: Active database session.
    """
    with Session(engine) as session:
        yield session

def get_test_session():
    """
    Provide a database session for testing.

    Yields:
        Session: Active test database session.
    """
    with Session(test_engine) as session:
        yield session

# ---------------------------
# Database initialization
# ---------------------------
def init_db(test=False):
    """
    Initialize the database schema.

    Creates all database tables based on SQLModel metadata.

    Args:
        test (bool): If True, initialize the test database.
                     Otherwise, initialize the production database.
    """
    if test:
        SQLModel.metadata.create_all(test_engine)
    else:
        SQLModel.metadata.create_all(engine)

# ---------------------------
# Database query helpers
# ---------------------------
def users_db(session: Session = Depends(get_session)):
    """
    Retrieve all users from the database.

    Args:
        session (Session): Database session dependency.

    Returns:
        list[User]: List of user records.
    """
    users = session.exec(select(User)).all()
    return users

def accounts_db(session: Session = Depends(get_session)):
    """
    Retrieve all accounts from the database.

    Args:
        session (Session): Database session dependency.

    Returns:
        list[Account]: List of account records.
    """
    accounts = session.exec(select(Account)).all()
    return accounts

def balances_db(session: Session = Depends(get_session)):
    """
    Retrieve all balance-related operations.

    This includes deposits, withdrawals, and transfers.

    Args:
        session (Session): Database session dependency.

    Returns:
        list: List of deposit, withdraw, and transfer records.
    """
    balances = session.exec(select(Deposit)).all()
    balances += session.exec(select(Withdraw)).all()
    balances += session.exec(select(Transfer)).all()
    return balances

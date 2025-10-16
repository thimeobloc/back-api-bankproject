from sqlmodel import SQLModel, create_engine, Session, select
from app.db.models import User, Account, Deposit, Withdraw, Transfer
from fastapi import Depends
from sqlalchemy.pool import StaticPool

DATABASE_URL = "sqlite:///database.db"
engine = create_engine(DATABASE_URL, echo=True)

TEST_DATABASE_URL = "sqlite:///:memory:"
test_engine = create_engine(
    TEST_DATABASE_URL,
    echo=True,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool
)

def get_session():
    with Session(engine) as session:
        yield session

def get_test_session():
    with Session(test_engine) as session:
        yield session

def init_db(test=False):
    if test:
        SQLModel.metadata.create_all(test_engine)
    else:
        SQLModel.metadata.create_all(engine)

def users_db(session: Session = Depends(get_session)):
    users = session.exec(select(User)).all()
    return users

def accounts_db(session: Session = Depends(get_session)):
    accounts = session.exec(select(Account)).all()
    return accounts

def balances_db(session: Session = Depends(get_session)):
    balances = session.exec(select(Deposit)).all()
    balances += session.exec(select(Withdraw)).all()
    balances += session.exec(select(Transfer)).all()
    return balances

from sqlmodel import SQLModel, Field, Column, TIMESTAMP, text, Relationship
from datetime import datetime
from typing import List, Optional

class User(SQLModel, table=True):
    __tablename__ = "users"
    id: int | None = Field(default=None, primary_key=True)
    name: str = Field(index=True)
    email: str = Field(index=True)
    password: str
    beneficiaries: List["Beneficiary"] = Relationship(back_populates="user")
    accounts: List["Account"] = Relationship(back_populates="user")

class Account(SQLModel, table=True):
    __tablename__ = "accounts"
    id: int = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="users.id")
    balance: float = Field(default=0.0)
    main: bool = Field(default=False)
    closed: bool = Field(default=False)
    status: bool = Field(default=False)
    rib: str = Field(index=True)
    deposits: List["Deposit"] = Relationship(back_populates="account")
    withdraws: List["Withdraw"] = Relationship(back_populates="account")
    transfers_sent: List["Transfer"] = Relationship(back_populates="from_account", sa_relationship_kwargs={"foreign_keys":"Transfer.from_account_id"})
    transfers_received: List["Transfer"] = Relationship(back_populates="to_account", sa_relationship_kwargs={"foreign_keys":"Transfer.to_account_id"})
    beneficiaries: List["Beneficiary"] = Relationship(back_populates="account")
    user: Optional[User] = Relationship(back_populates="accounts")

class Beneficiary(SQLModel, table=True):
    __tablename__ = "beneficiaries"
    id: int | None = Field(default=None, primary_key=True)
    rib: str
    name: str
    user_id: int = Field(foreign_key="users.id")
    account_id: int = Field(foreign_key="accounts.id")
    user: Optional[User] = Relationship(back_populates="beneficiaries")
    account: Optional[Account] = Relationship(back_populates="beneficiaries")

class Deposit(SQLModel, table=True):
    __tablename__ = "deposits"
    id: int = Field(default=None, primary_key=True)
    account_id: int = Field(foreign_key="accounts.id")
    amount: float = Field(default=0.0)
    type: str = Field(default="deposit")
    date: Optional[datetime] = Field(sa_column=Column(TIMESTAMP(timezone=True), nullable=False, server_default=text("CURRENT_TIMESTAMP")))
    account: Optional[Account] = Relationship(back_populates="deposits")

class Withdraw(SQLModel, table=True):
    __tablename__ = "withdraws"
    id: int = Field(default=None, primary_key=True)
    account_id: int = Field(foreign_key="accounts.id")
    amount: float = Field(default=0.0)
    type: str = Field(default="withdraw")
    date: Optional[datetime] = Field(sa_column=Column(TIMESTAMP(timezone=True), nullable=False, server_default=text("CURRENT_TIMESTAMP")))
    account: Optional[Account] = Relationship(back_populates="withdraws")

class Transfer(SQLModel, table=True):
    __tablename__ = "transfers"
    id: int = Field(default=None, primary_key=True)
    from_account_id: int = Field(foreign_key="accounts.id")
    to_account_id: int = Field(foreign_key="accounts.id")
    amount: float = Field(default=0.0)
    status: str = Field(default="pending")
    type: str = Field(default="transfer")
    date: Optional[datetime] = Field(sa_column=Column(TIMESTAMP(timezone=True), nullable=False, server_default=text("CURRENT_TIMESTAMP")))
    from_account: Optional[Account] = Relationship(back_populates="transfers_sent", sa_relationship_kwargs={"foreign_keys":"Transfer.from_account_id"})
    to_account: Optional[Account] = Relationship(back_populates="transfers_received", sa_relationship_kwargs={"foreign_keys":"Transfer.to_account_id"})

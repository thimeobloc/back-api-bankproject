"""
Database models definition.

This module defines all SQLModel entities used by the application,
including users, accounts, beneficiaries, deposits, withdrawals,
and transfers. These models represent the database schema and
their relationships.
"""

from datetime import datetime
from typing import Optional, List
from sqlmodel import SQLModel, Field, Column, TIMESTAMP, text, Relationship

# ---------------------------
# Constants
# ---------------------------
ACCOUNTS_TABLE_ID = "accounts.id"
"""
Foreign key reference to the accounts table primary key.
"""

# ---------------------------
# User model
# ---------------------------
class User(SQLModel, table=True):
    """
    User entity.

    Represents an application user who owns accounts and beneficiaries.
    """

    __tablename__ = "users"

    id: Optional[int] = Field(default=None, primary_key=True)
    """Unique identifier of the user."""

    name: str = Field(index=True)
    """User full name."""

    email: str = Field(index=True)
    """User email address."""

    password: str = Field(index=True)
    """Hashed user password."""

    beneficiaries: List["Beneficiary"] = Relationship(back_populates="user")
    """List of beneficiaries associated with the user."""

# ---------------------------
# Beneficiary model
# ---------------------------
class Beneficiary(SQLModel, table=True):
    """
    Beneficiary entity.

    Represents a beneficiary that can receive transfers from an account.
    """

    __tablename__ = "beneficiaries"

    id: Optional[int] = Field(default=None, primary_key=True)
    """Unique identifier of the beneficiary."""

    rib: str = Field(index=True)
    """Bank RIB of the beneficiary."""

    name: str = Field(index=True)
    """Display name of the beneficiary."""

    user_id: int = Field(index=True, foreign_key="users.id")
    """Identifier of the user owning this beneficiary."""

    account_id: int = Field(foreign_key=ACCOUNTS_TABLE_ID)
    """Identifier of the linked account."""

    user: Optional[User] = Relationship(back_populates="beneficiaries")
    """Associated user."""

    account: Optional["Account"] = Relationship(back_populates="beneficiaries")
    """Associated account."""

# ---------------------------
# Account model
# ---------------------------
class Account(SQLModel, table=True):
    """
    Bank account entity.

    Represents a user bank account used for deposits, withdrawals,
    and transfers.
    """

    __tablename__ = "accounts"

    id: int = Field(primary_key=True)
    """Unique identifier of the account."""

    user_id: int = Field(index=True, foreign_key="users.id")
    """Owner user identifier."""

    balance: float = Field(default=0.0)
    """Current account balance."""

    main: bool = Field(default=False)
    """Indicates whether this account is the main account."""

    closed: bool = Field(default=False)
    """Indicates whether the account is closed."""

    status: bool = Field(default=False)
    """Indicates whether the account has ongoing operations."""

    rib: str = Field(index=True)
    """Bank RIB of the account."""

    type: str = Field(default="Compte courant")
    """Type of account (e.g., current account)."""

    date: Optional[datetime] = Field(
        sa_column=Column(
            TIMESTAMP(timezone=True),
            nullable=False,
            server_default=text("CURRENT_TIMESTAMP")
        )
    )
    """Account creation date."""

    deposits: List["Deposit"] = Relationship(back_populates="account")
    """List of deposits made on this account."""

    withdraws: List["Withdraw"] = Relationship(back_populates="account")
    """List of withdrawals made from this account."""

    transfers_sent: List["Transfer"] = Relationship(
        back_populates="from_account",
        sa_relationship_kwargs={"foreign_keys": "Transfer.from_account_id"}
    )
    """Transfers sent from this account."""

    transfers_received: List["Transfer"] = Relationship(
        back_populates="to_account",
        sa_relationship_kwargs={"foreign_keys": "Transfer.to_account_id"}
    )
    """Transfers received by this account."""

    beneficiaries: List["Beneficiary"] = Relationship(back_populates="account")
    """Beneficiaries linked to this account."""

# ---------------------------
# Deposit model
# ---------------------------
class Deposit(SQLModel, table=True):
    """
    Deposit entity.

    Represents a deposit operation performed on an account.
    """

    __tablename__ = "deposits"

    id: int = Field(primary_key=True)
    """Unique identifier of the deposit."""

    account_id: int = Field(index=True, foreign_key=ACCOUNTS_TABLE_ID)
    """Associated account identifier."""

    amount: float = Field(default=0.0, index=True)
    """Deposit amount."""

    type: str = Field(default="deposit", index=True)
    """Operation type."""

    date: Optional[datetime] = Field(
        sa_column=Column(TIMESTAMP(timezone=True), nullable=False, server_default=text("CURRENT_TIMESTAMP"))
    )
    """Deposit date."""

    account: Optional[Account] = Relationship(back_populates="deposits")
    """Related account."""

# ---------------------------
# Withdraw model
# ---------------------------
class Withdraw(SQLModel, table=True):
    """
    Withdraw entity.

    Represents a withdrawal operation from an account.
    """

    __tablename__ = "withdraws"

    id: int = Field(primary_key=True)
    """Unique identifier of the withdrawal."""

    account_id: int = Field(index=True, foreign_key=ACCOUNTS_TABLE_ID)
    """Associated account identifier."""

    amount: float = Field(default=0.0, index=True)
    """Withdrawal amount."""

    type: str = Field(default="withdraw", index=True)
    """Operation type."""

    date: Optional[datetime] = Field(
        sa_column=Column(TIMESTAMP(timezone=True), nullable=False, server_default=text("CURRENT_TIMESTAMP"))
    )
    """Withdrawal date."""

    account: Optional[Account] = Relationship(back_populates="withdraws")
    """Related account."""

# ---------------------------
# Transfer model
# ---------------------------
class Transfer(SQLModel, table=True):
    """
    Transfer entity.

    Represents a transfer operation between two accounts.
    """

    __tablename__ = "transfers"

    id: int = Field(primary_key=True)
    """Unique identifier of the transfer."""

    from_account_id: int = Field(foreign_key=ACCOUNTS_TABLE_ID)
    """Sender account identifier."""

    to_account_id: int = Field(foreign_key=ACCOUNTS_TABLE_ID)
    """Recipient account identifier."""

    amount: float = Field(default=0.0)
    """Transfer amount."""

    status: str = Field(default="pending")
    """Transfer status (pending, completed, aborted)."""

    type: str = Field(default="transfer", index=True)
    """Operation type."""

    date: Optional[datetime] = Field(
        sa_column=Column(TIMESTAMP(timezone=True), nullable=False, server_default=text("CURRENT_TIMESTAMP"))
    )
    """Transfer creation date."""

    from_account: Optional[Account] = Relationship(
        back_populates="transfers_sent",
        sa_relationship_kwargs={"foreign_keys": "Transfer.from_account_id"}
    )
    """Sender account."""

    to_account: Optional[Account] = Relationship(
        back_populates="transfers_received",
        sa_relationship_kwargs={"foreign_keys": "Transfer.to_account_id"}
    )
    """Recipient account."""

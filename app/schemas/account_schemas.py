from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from datetime import datetime

# Liste des types de comptes épargne autorisés
ACCOUNT_TYPES = [
    "Livret A",
    "LDDS",
    "Livret Jeune",
    "PEL",
    "Compte à terme",
    "Assurance-vie"
]

class AccountBase(BaseModel):
    """Base schema for account"""
    user_id: int
    balance: float = 0.0
    main: bool = False
    deposit: List[Dict[str, Any]] = Field(default_factory=list)
    withdraw: List[Dict[str, Any]] = Field(default_factory=list)
    transfer: List[Dict[str, Any]] = Field(default_factory=list)
    beneficiary: List[Dict[str, Any]] = Field(default_factory=list)
    date: Optional[datetime] = None 
    closed: bool = False
    status: bool = False
    rib: str = ""
    type: str = "Compte courant"

class AccountCreate(BaseModel):
    """Schema for creating an account"""
    account_type: str  # Champ pour le type de compte choisi

class AccountOut(AccountBase):
    """Schema for outputting account information"""
    id: int

class beneficiary(BaseModel):
    """Schema for a beneficiary"""
    rib: str
    name: str
    user_id: int
    date: Optional[datetime] = None
class BeneficiaryCreate(BaseModel):
    rib: str
    name: str

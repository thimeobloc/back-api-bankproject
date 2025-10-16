from pydantic import BaseModel, Field
from typing import List, Dict, Any
from datetime import datetime
from typing import Optional


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

class AccountCreate(AccountBase):
    """Schema for creating an account"""
    pass  

class AccountOut(AccountBase):
    """Schema for outputting account information"""
    id: int

class beneficiary(BaseModel):
    """Schema for a beneficiary"""
    rib: str
    name: str
    user_id: int
    date: Optional[datetime] = None 




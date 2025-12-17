from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class DepositCreate(BaseModel):
    """Schema for deposit creation"""
    user_id: int
    account_id: int
    amount: float
    date: Optional[datetime] = None  

class WithdrawCreate(BaseModel):
    """Schema for withdraw creation"""
    user_id: int
    account_id: int
    amount: float
    date: Optional[datetime] = None 

class TransferCreate(BaseModel):
    """Schema for transfer creation"""
    from_account_id: int
    to_account_id: int
    amount: float
    date: Optional[datetime] = None 

class TransferResponse(TransferCreate):
    """Schema for transfer response"""
    id: int
    status: str
    expiry: Optional[datetime] = None

class TransferByRIB(BaseModel):
    from_account_id: int
    to_rib: str
    amount: float

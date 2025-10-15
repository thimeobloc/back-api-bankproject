from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class depositCreate(BaseModel):
    account_id: int
    amount: float
    date: Optional[datetime] = None  

class transferCreate(BaseModel):
    from_account_id: int
    to_account_id: int
    amount: float
    date: Optional[datetime] = None  # automatique si non fournie

class withdrawCreate(BaseModel):
    account_id: int
    amount: float
    date: Optional[datetime] = None  # automatique si non fournie

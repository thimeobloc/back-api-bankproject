from pydantic import BaseModel
from datetime import datetime


class depositCreate(BaseModel):
    id: int
    account_id: int
    amount: float
    date: datetime

class withdrawCreate(BaseModel):
    id: int
    account_id: int
    amount: float
    date: datetime

class transferCreate(BaseModel):
    id: int
    from_account_id: int
    to_account_id: int
    amount: float
    date: datetime
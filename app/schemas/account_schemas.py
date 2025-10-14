from pydantic import BaseModel, Field
from typing import List

class AccountBase(BaseModel):
    user_id: int
    balance: float = 0.0
    deposit: list = []
    withdraw: list = []
    transfer: list = []

class AccountCreate(AccountBase):
    pass  

class AccountOut(AccountBase):
    id: int

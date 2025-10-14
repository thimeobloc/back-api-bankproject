from pydantic import BaseModel, Field
from typing import List, Dict, Any

class AccountBase(BaseModel):
    user_id: int
    balance: float = 0.0
    deposit: List[Dict[str, Any]] = Field(default_factory=list)
    withdraw: List[Dict[str, Any]] = Field(default_factory=list)
    transfer: List[Dict[str, Any]] = Field(default_factory=list)

class AccountCreate(AccountBase):
    pass  # pas d'id ici à la création

class AccountOut(AccountBase):
    id: int

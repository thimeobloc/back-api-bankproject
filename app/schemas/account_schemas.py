from pydantic import BaseModel, Field
from typing import List, Dict, Any
from datetime import datetime
from typing import Optional


class AccountBase(BaseModel):
    user_id: int
    balance: float = 0.0
    main: bool = False
    deposit: List[Dict[str, Any]] = Field(default_factory=list)
    withdraw: List[Dict[str, Any]] = Field(default_factory=list)
    transfer: List[Dict[str, Any]] = Field(default_factory=list)
    date: Optional[datetime] = None  # automatique si non fournie
    closed: bool = False

class AccountCreate(AccountBase):
    pass  

class AccountOut(AccountBase):
    id: int

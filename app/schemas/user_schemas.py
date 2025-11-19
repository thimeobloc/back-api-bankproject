from pydantic import BaseModel, EmailStr

class UserBase(BaseModel):
    """Base schema for user information"""
    name: str
    email: EmailStr

class UserCreate(UserBase):
    """Schema for creating a new user"""
    password: str  

class UserOut(UserBase):
    """Schema for outputting user information without password"""
    id: int
    model_config = {"from_attributes": True}

class LoginSchema(BaseModel):
    """Schema for login"""
    email: EmailStr
    password: str

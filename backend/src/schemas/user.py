from pydantic import BaseModel, EmailStr, Field
from uuid import UUID
from datetime import datetime
from typing import Optional

class UserBase(BaseModel):
    email: EmailStr = Field(..., description='User Email')
    full_name: str = Field(..., min_length=1, max_length=255, description='Full Name')

class UserCreate(UserBase):
    password: str = Field(..., min_length=8, max_length=255, description='Password')

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserUpdate(BaseModel):
    full_name: Optional[str] = Field(..., min_length=1, max_length=255)
    email: Optional[EmailStr] = None

class UserResponse(UserBase):
    id: UUID
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes: True

class UserMeResponse(UserResponse):
    pass

class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = 'bearer'

class TokenRefresh(BaseModel):
    refresh_token: str
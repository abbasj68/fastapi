from pydantic import BaseModel,EmailStr
from typing import Optional

class UserCreate(BaseModel):
    name : Optional[str] = None
    username: str
    email: EmailStr
    location : Optional[str] = None
    password: str

class UserLogin(BaseModel):
    username: str
    password: str


class Token(BaseModel):
    access_token: str
    token_type: str

class TokenRefresh(BaseModel):
    refresh_token : str
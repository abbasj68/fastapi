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

class UserProfile(BaseModel):
    id : int
    username : str
    email : str
    is_superuser : bool
    
    class config:
        orm_mode = True
        
class ProfileUpdate(BaseModel):
    name : Optional[str] =  None
    email: Optional[EmailStr] = None
    location: Optional[str] = None
    
class ChangePassword(BaseModel):
    old_password : str
    new_password : str
class Token(BaseModel):
    access_token: str
    token_type: str

class TokenRefresh(BaseModel):
    refresh_token : str
    
class CafeCreate(BaseModel):
    name : str
    address : str
    latitude :float
    longitude :float

class CafeOut(BaseModel):
    id : int
    name : str
    address : str
    latitude : float
    longitude : float
    
    class config:
        orm_mode = True
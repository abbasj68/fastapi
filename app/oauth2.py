from jose import JWTError,jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer,OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from . import models ,database , config
from datetime import datetime

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

def decode_access_token(token:str):
    try:
        payload = jwt.decode(token,config.SECRET_KEY, algorithms=[config.ALGORITHM])
        return payload
    except JWTError:
        return None
    
def is_token_revoked(token: str , db:Session) -> bool:
    return db.query(models.TokenBlocklist).filter(models.TokenBlocklist.token == token).first() is not None
    
def get_current_user(token: str =Depends(oauth2_scheme),db : Session = Depends(database.get_db)):
    credentials_exception =HTTPException(
        status_code=401,
        detail="Could not validate credentials"
    )
    try:
        payload = jwt.decode(token, config.SECRET_KEY, algorithms=[config.ALGORITHM])
        username : str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    user = db.query(models.User).filter(models.User.username == username).first()
    if user is None:
        raise credentials_exception
    return user
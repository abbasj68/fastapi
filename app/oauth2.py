from jose import JWTError,jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer,OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from . import models ,database , config
from .models import TokenBlocklist
from datetime import datetime

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")
oauth2_refresh_scheme =OAuth2PasswordBearer(tokenUrl="refresh")

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
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"www-Authenticate":"Bearer"},
    )
    try:
        payload = jwt.decode(token, config.SECRET_KEY, algorithms=[config.ALGORITHM])
        username : str = payload.get("sub")
        jti : str = payload.get("jti")
        if username is None or jti is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    blocked_token = db.query(TokenBlocklist).filter_by(jti=jti).first()
    if blocked_token:
        raise HTTPException(status_code=401, detail="Token revoked")
    
    user = db.query(models.User).filter(models.User.username == username).first()
    if user is None:
        raise credentials_exception
    return user

def get_current_user_from_refresh(
    token: str = Depends(oauth2_refresh_scheme),
    db: Session = Depends(database.get_db)
):
    try:
        payload = jwt.decode(token, config.SECRET_KEY, algorithms=[config.ALGORITHM])
        token_type = payload.get("type")
        if token_type != "refresh":
            raise HTTPException(status_code=401, detail="Token is not a refresh token")
        
        user_id: str = payload.get("sub")
        jti: str = payload.get("jti")
        
        if user_id is None or jti is None:
            raise HTTPException(status_code=401, detail="Invalid refresh token")
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid refresh token")

    user = db.query(models.User).filter(models.User.id == int(user_id)).first()
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return user
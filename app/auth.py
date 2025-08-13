from fastapi import HTTPException, Request
from sqlalchemy.orm import session
from app import models, schemas, utils ,config
from .models import TokenBlocklist
from jose import jwt
from datetime import datetime, timedelta
import uuid
from fastapi import Depends
from app import database
from fastapi.security import OAuth2PasswordRequestForm,OAuth2PasswordBearer

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")
def signup(user_data:schemas.UserCreate , db:session):
    
    if db.query(models.User).filter(models.User.username == user_data.username).first():
        raise HTTPException(status_code=400 ,detail="Username already exists")
    
    if db.query(models.User).filter(models.User.email == user_data.email).first():
        raise HTTPException(status_code=400 , detail="Email already exists")
    
    
    hashed = utils.hash_password(user_data.password)
    user = models.User(
        username=user_data.username,
        email=user_data.email,
        hashed_password=hashed,
        name = user_data.name,
        location = user_data.location
    )

    db.add(user)
    db.commit()
    db.refresh(user)

    return {"message": "User registered successfully"}

def create_access_token(data: dict, expires_delta:timedelta=None):
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=config.ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({
        "exp":expire,
        "type":"access",
        "iat": datetime.utcnow(),
        "jti": str(uuid.uuid4())
    })
    encoded_jwt = jwt.encode(to_encode , config.SECRET_KEY, algorithm=config.ALGORITHM)
    return encoded_jwt

def create_refresh_token(user_id: int, expires_delta: timedelta = None):
    expire = datetime.utcnow() + (expires_delta or timedelta(days=config.ACCESS_TOKEN_EXPIRE_DAY))
    to_encode = {
        "sub": str(user_id),
        "type": "refresh",
        "exp": expire,
        "iat": datetime.utcnow(),
        "jti": str(uuid.uuid4())
    }
    return jwt.encode(to_encode, config.SECRET_KEY, algorithm=config.ALGORITHM)
def login(user_data: OAuth2PasswordRequestForm = Depends() , db:session = Depends(database.get_db)):
    user = db.query(models.User).filter(models.User.username == user_data.username).first()

    if not user or not utils.verify_password(user_data.password, user.hashed_password):
        raise HTTPException(status_code=400 ,detail="Invalid username or password")
    
    access_token = create_access_token(data={"sub": user.username})
    refresh_token = create_refresh_token(user_id=user.id)

    db_token = TokenBlocklist(token=access_token ,user_id=user.id)
    db.add(db_token)
    db.commit()
    
    return {
        "access_token": access_token,
        "refresh_token":refresh_token,
        "token_type": "Bearer",
        "message": "Login Successful"
    }




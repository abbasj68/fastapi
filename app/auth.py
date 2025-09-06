from fastapi import HTTPException, Request ,status
from sqlalchemy.orm import session
from app import schemas, utils ,config
from app.models import User
from .models import TokenBlocklist
from .oauth2 import get_current_user
from jose import jwt,JWTError
from datetime import datetime, timedelta
import uuid
from fastapi import Depends
from app.database import get_db
from fastapi.security import OAuth2PasswordRequestForm,OAuth2PasswordBearer


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")
def signup(user_data:schemas.UserCreate , db:session):
    
    if db.query(User).filter(User.username == user_data.username).first():
        raise HTTPException(status_code=400 ,detail="این نام کاربری وجود دارد.")
    
    if db.query(User).filter(User.email == user_data.email).first():
        raise HTTPException(status_code=400 , detail="این ایمیل وجود دارد.")
    
    
    hashed = utils.hash_password(user_data.password)
    user = User(
        username=user_data.username,
        email=user_data.email,
        hashed_password=hashed,
        name = user_data.name,
        location = user_data.location,
        is_superuser = False
    )

    db.add(user)
    db.commit()
    db.refresh(user)

    return {"message": "User signup successfully"}

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
    expire = datetime.utcnow() + (expires_delta or timedelta(days=config.REFRESH_TOKEN_EXPIRE_DAYS))
    to_encode = {
        "sub": str(user_id),
        "type": "refresh",
        "exp": expire,
        "iat": datetime.utcnow(),
        "jti": str(uuid.uuid4())
    }
    encoded_ref_jwt = jwt.encode(to_encode, config.SECRET_KEY, algorithm=config.ALGORITHM)
    return encoded_ref_jwt

def save_refresh_token(db: session, user_id :int , token: str, jti: str,exp: int):
    token_entry = db.query(TokenBlocklist).filter_by(user_id=user_id).first()
    
    if token_entry:
        token_entry.token = token
        token_entry.jti = jti
        token_entry.expires_at = datetime.utcfromtimestamp(exp)
        token_entry.revoked = False
    else:
        token_entry = TokenBlocklist(
            user_id = user_id,
            token = token,
            jti = jti,
            expires_at = datetime.utcfromtimestamp(exp),
            revoked = False,
            create_at = datetime.utcnow()
        )
        db.add(token_entry)
        
    db.commit()
    db.refresh(token_entry)
    return token_entry

def login(user_data: schemas.UserProfile, db:session = Depends(get_db)):
    user = db.query(User).filter(User.username == user_data.username).first()

    if not user or not utils.verify_password(user_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST ,
            detail="Invalid username or password" ,
            )
    
    access_token = create_access_token(data={"sub": user.username})
    refresh_token = create_refresh_token(user_id=user.id)

    try:
        refresh_payload = jwt.decode(refresh_token,config.SECRET_KEY , algorithms=[config.ALGORITHM])
        jti_form_token = refresh_payload.get("jti")
        exp = refresh_payload.get("exp")
        if not jti_form_token:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Could not retrieve JTI from refresh token.",
            )
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error decoding refresh token",
        )
    db_refresh_token = db.query(TokenBlocklist).filter_by(user_id=user.id).first()
    if db_refresh_token:
        db_refresh_token.token = refresh_token
        db_refresh_token.jti = jti_form_token
        db_refresh_token.expires_at = datetime.utcfromtimestamp(exp)
        db_refresh_token.revoked = False
        db_refresh_token.created_at = datetime.utcnow()
    else:
        db_refresh_token = TokenBlocklist(
            token=refresh_token,
            jti = jti_form_token,
            user_id=user.id,
            created_at = datetime.utcnow() + timedelta(days=config.REFRESH_TOKEN_EXPIRE_DAYS)
            )
        db.add(db_refresh_token)
    db.commit()
    db.refresh(db_refresh_token)
    
    return {
        "access_token": access_token,
        "refresh_token":refresh_token,
        "token_type": "Bearer",
        "message": "Login Successful"
    }
    
def get_profile(current_user: User= Depends(get_current_user)):
    return{
        "id":current_user.id,
        "username":current_user.username,
        "email":current_user.email,
        "name":current_user.name,
        "location":current_user.location,
        "is_superuser":current_user.is_superuser,
    }
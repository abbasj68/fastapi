from fastapi import FastAPI, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import SessionLocal, engine ,get_db
from app.models import Base, User ,TokenBlocklist
from typing import Union
from pydantic import BaseModel
from typing import Annotated
from fastapi.security import OAuth2PasswordBearer,OAuth2PasswordRequestForm
from app import models , schemas , database, utils ,config , oauth2
from app.oauth2 import oauth2_scheme, get_current_user, get_current_user_from_refresh
from datetime import datetime

from app import auth
from .schemas import TokenRefresh
from jose import jwt,JWTError 
from .scheduler import start_scheduler
from sqlalchemy import text
from app.schemas import CafeOut, CafeCreate
from app.models import Cafe
from app.routers import cafe
from . import profile
import uuid

app= FastAPI()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")
oauth2_refresh_scheme = OAuth2PasswordBearer(tokenUrl="refresh")
models.Base.metadata.create_all(bind=database.engine)

app.include_router(cafe.router)
app.include_router(profile.router)


@app.post('/signup')
def signup_user(user: schemas.UserCreate ,db: Session=Depends(get_db)):
    return auth.signup(user , db)

@app.post('/login')
def login_json(user: schemas.UserLogin , db: Session=Depends(get_db)):
    return auth.login(user , db)

'''@app.post("/login")
async def login_user(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(database.get_db)):
    return auth.login(form_data, db)'''
@app.post("/logout")
def logout_user(token :str =Depends(oauth2_refresh_scheme),db : Session = Depends(get_db), current_user:User = Depends(get_current_user_from_refresh)):
    try:
        payload = jwt.decode(token, config.SECRET_KEY, algorithms=[config.ALGORITHM])
        token_type = payload.get("type")
        exp = payload.get("exp")
        user_id: str = payload.get('sub')
        jti:str = payload.get('jti')
        if token_type != "refresh":
            raise HTTPException(status_code=401, detail="Invalid token type, must be refresh")
        
        if user_id is None or jti is None:
            raise HTTPException(status_code=401, detail="Invalid refresh token")

    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid refresh token")
    
    user = db.query(User).filter(User.id == int(user_id)).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    token_entry = db.query(TokenBlocklist).filter_by(jti=jti).first()
    if token_entry:
        if not token_entry.revoked: 
            token_entry.revoked = True
            if not token_entry.expires_at:
                token_entry.expires_at = datetime.utcfromtimestamp(exp)
            db.commit()      
    else:
        new_token = TokenBlocklist(
            token = token,
            jti = jti , 
            user_id = current_user.id,
            revoked = True,
            created_at = datetime.utcnow(),
            expires_at = datetime.utcfromtimestamp(exp)
        )
        db.add(new_token)
        db.commit()
    return {"message":"Logout Successful"}

@app.post('/refresh')
def refresh_token(data: TokenRefresh , db: Session = Depends(get_db)):
    refresh_token_str=data.refresh_token
    try:
        payload = jwt.decode(refresh_token_str , config.SECRET_KEY ,algorithms=[config.ALGORITHM])
        user_id = int(payload.get("sub"))
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, 
                detail="Invalid refresh token",
                )
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token",
        )       
    stored_token = db.query(TokenBlocklist).filter(
        TokenBlocklist.token == refresh_token_str,
        TokenBlocklist.revoked == False
    ).first()
    if not stored_token :
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token not found or already revoked",
        )
    user = db.query(User).get(user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
            )
    
    new_access_token = auth.create_access_token(data={"sub": user.username})
    stored_token.revoked = True
    db.commit()
    
    new_refresh_token = auth.create_refresh_token(user_id=user.id)
    db_refresh_token = TokenBlocklist(token=new_refresh_token, user_id=user.id, jti = str(uuid.uuid4()))
    db.add(db_refresh_token)
    db.commit()
    db.refresh(db_refresh_token)
    return{
        "access_token":new_access_token,
        "token_type": "Bearer",
        "refresh_token": new_refresh_token
    }
@app.delete('/users/{user_id}',status_code=status.HTTP_204_NO_CONTENT)
async def hard_delete_users(user_id: int, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException (status_code=404, detail="User not found")
    db.delete(user)
    db.commit()
    return {"messages":"User marked as deleted successfully"}

@app.delete("/token/clear")
def clear_tokens(db : Session = Depends(get_db)):
    deleted_count = db.query(TokenBlocklist).delete()
    db.commit()
    return {"message": f"{deleted_count} Tokens deleted." }
    

@app.post("/cafes/",response_model=CafeOut)
def create_cafe(cafe: CafeCreate,db: Session=Depends(get_db)):
    point_wkt = f"POINT({cafe.longitude} {cafe.latitude})"
    new_cafe = Cafe(
        name = cafe.name,
        address = cafe.address,
        location = text(f"ST_GeomFromText('{point_wkt}', 4326)")
    )
    db.add(new_cafe)
    db.commit()
    db.refresh(new_cafe)
    
    coords = db.execute(
        text(f"SELECT ST_X(location) AS lon, ST_Y(location) AS lat FROM cafes WHERE id = {new_cafe.id}")
    ).mappings().first()
    
    return CafeOut(
        id = new_cafe.id,
        name = new_cafe.name,
        address = new_cafe.address,
        latitude = coords["lat"],
        longitude = coords["lon"],
    )

@app.get("/cafes/{cafe_id}",response_model=CafeOut)
def get_cafe(cafe_id: int, db: Session =Depends(get_db)):
    cafe = db.query(Cafe).filter(Cafe.id == cafe_id).first()
    if not cafe:
        raise HTTPException(status_code=404, detail="Cafe not found")
    
    coords = db.execute(
        text(f"SELECT ST_X(location) AS lon, ST_Y(location) AS lat FROM cafes WHERE id = {cafe.id}")
    ).mappings().first()
    
    return CafeOut(
        id = cafe.id,
        name = cafe.name,
        address = cafe.address,
        latitude = coords["lat"],
        longitude = coords["lon"],
    )



@app.get("/")
def read_root():
    return {"message": "Hello World"}

@app.on_event("startup")
def startup_event():
    start_scheduler()

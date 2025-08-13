from fastapi import FastAPI, Depends, HTTPException, status , Body
from sqlalchemy.orm import Session
from app.database import SessionLocal, engine
from app.models import Base, User ,TokenBlocklist
from typing import Union
from pydantic import BaseModel
from typing import Annotated
from fastapi.security import OAuth2PasswordBearer,OAuth2PasswordRequestForm
from app import models , schemas , auth, database, utils ,config , oauth2
from app.oauth2 import oauth2_scheme, get_current_user
from datetime import datetime
from .schemas import TokenRefresh
from jose import jwt,JWTError


app= FastAPI()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")
models.Base.metadata.create_all(bind=database.engine)


@app.post('/signup')
def signup_user(user: schemas.UserCreate ,db: Session=Depends(database.get_db)):
    return auth.signup(user , db)

@app.post('/login')
def login_json(user: schemas.UserLogin , db: Session=Depends(database.get_db)):
    return auth.login(user , db)

'''@app.post("/login")
async def login_user(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(database.get_db)):
    return auth.login(form_data, db)'''
@app.post("/logout")
def logout_user(token :str =Depends(oauth2_scheme),db : Session = Depends(database.get_db), current_user = Depends(get_current_user)):
    try:
        payload = jwt.decode(token, config.SECRET_KEY, algorithms=[config.ALGORITHM])
        username = payload.get('sub')
        if username is None or username != current_user.username:
            raise HTTPException(status_code=401, detail="Invalid token")
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    token_entry = db.query(TokenBlocklist).filter_by(token=token).first()
    if token_entry:
        if token_entry.revoked:
            raise HTTPException(status_code=400 , detail="Token alreay revoked")
        token_entry.revoked = True
        db.commit()
        return {"message": "Token revoked"}
    
    new_token = TokenBlocklist(
        token = token,
        user_id = current_user.id,
        revoked = True,
        created_at = datetime.utcnow()
    )
    db.add(new_token)
    db.commit()
    return {"message":"Logout Successful"}

@app.post('/refresh')
def refresh_token(data: TokenRefresh , db: Session = Depends(database.get_db)):
    refresh_token=data.refresh_token
    try:
        payload = jwt.decode(refresh_token , config.SECRET_KEY ,algorithms=[config.ALGORITHM])
        username = payload.get("sub")
        if not username:
            raise HTTPException(status_code=401, detail="Invalid token")
        
        # if oauth2.is_token_revoked(refresh_token, db):
        #     raise HTTPException(status_code=401, detail="Token has been revoked")

        user = db.query(models.User).filter(models.User.username == username).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        new_access_token = auth.create_access_token(data={"sub": username})
        return {
            "access_token": new_access_token,
            "token_type":"Bearer"
        }
    
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")
    
@app.get("/profile")
def read_profile(current_user: models.User = Depends(get_current_user)):
    return {"username": current_user.username, "email": current_user.email}

@app.get("/")
def read_root():
    return {"message": "FastAPI is working"}




'''fake_users_db = {
    "johndoe": {
        "username": "johndoe",
        "full_name": "John Doe",
        "email": "johndoe@example.com",
        "hashed_password": "fakehashedsecret",
        "disabled": False,
    },
    "alice": {
        "username": "alice",
        "full_name": "Alice Wonderson",
        "email": "alice@example.com",
        "hashed_password": "fakehashedsecret2",
        "disabled": True,
    },
}
'''

'''# ساخت جداول
Base.metadata.create_all(bind=engine)

app = FastAPI()
users={}
def fake_hash_password(password: str):
    return "fakehashed" + password
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")'''

'''class Item(BaseModel):
    name: str
    price: float
    is_offer: Union[bool, None] = None

class UserCreate(BaseModel):
    username: str
    email: str | None = None
    full_name : str | None = None
    disabled : bool | None = None

class UserInDB(User):
    hashed_password: str
'''
'''
def get_user(db, username: str):
    if username in db:
        user_dict = db[username]
        return UserInDB(**user_dict)
'''

'''def fake_decode_token(token):
    # This doesn't provide any security at all
    # Check the next version
    user = get_user(fake_users_db, token)
    return user'''


'''async def get_current_user(token: Annotated[str, Depends(oauth2_scheme)]):
    user = fake_decode_token(token)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user


async def get_current_active_user(
    current_user: Annotated[User, Depends(get_current_user)],
):
    if current_user.disabled:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user

@app.post("/token")
async def login(form_data: Annotated[OAuth2PasswordRequestForm, Depends()]):
    user_dict = fake_users_db.get(form_data.username)
    if not user_dict:
        raise HTTPException(status_code=400, detail="Incorrect username or password")
    user = UserInDB(**user_dict)
    hashed_password = fake_hash_password(form_data.password)
    if not hashed_password == user.hashed_password:
        raise HTTPException(status_code=400, detail="Incorrect username or password")

    return {"access_token": user.username, "token_type": "bearer"}
'''
'''
class UserResponse(BaseModel):
    id: int
    name: str
    email: str

    class Config:
        orm_mode= True

@app.post("/users/",response_model=UserResponse)
def create_user(user:UserCreate):
    db: Session = SessionLocal()
    db_user = User(name=user.name, email=user.email)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    db.close()
    return db_user


# Dependency برای گرفتن session از دیتابیس
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.get("/")
def read_root():
    return {"hello":"world"}


@app.post("/users/")
def create_user(name: str, email: str, db: Session = Depends(get_db)):
    user = User(name=name, email=email)
    db.add(user)
    db.commit()
    db.refresh(user)
    return (user)

@app.get("/users/{user_id}")
def read_user(user_id: int, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="کاربر پیدا نشد")
    return user

@app.put("/users/{user_id}")
def update_item(item_id: int, item: Item):
    return {"item_name": item.name, "item_id": item_id}

@app.get("/items/")
async def read_items(token: Annotated[str, Depends(oauth2_scheme)]):
    return {"token": token}

def fake_decode_token(token):
    return UserCreate(
        username=token +"fakedecoded", email="abbasj@gmail.com" ,full_name="abbas jamali"
    )

async def get_current_user(token: str = Depends(oauth2_scheme)):
    user = fake_decode_token(token)
    return user
@app.get("/userss/me")
async def read_user_me(curret_user: User = Depends(get_current_user)):
    return curret_user'''

'''@app.get("/users1/me")
async def read_users_me(
    current_user: Annotated[User, Depends(get_current_active_user)],
):
    return current_user'''
import datetime
from sqlalchemy import Column, Integer, String , DateTime, Text , ForeignKey,Boolean
from sqlalchemy.orm import relationship
from pydantic import BaseModel, EmailStr
from .database import Base

class User(Base):
    __tablename__ = "users"
    __allow_unmapped__ = True

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(20), nullable=True)
    username = Column(String(50), unique=True ,nullable=False)
    email = Column(String(255) ,unique=True, nullable=False)
    location = Column(String(25))
    hashed_password = Column(String(130),nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)

    tokens = relationship('TokenBlocklist' ,back_populates='user')


class TokenBlocklist(Base):
    __tablename__ = "token"
    __allow_unmapped__ = True

    id = Column(Integer,primary_key=True , index=True)
    token = Column(String(512), unique=True, nullable=False)
    user_id = Column(Integer , ForeignKey("users.id"))
    created_at = Column(DateTime , default=datetime.datetime.utcnow)
    revoked = Column(Boolean , default=False)

    user = relationship('User', back_populates='tokens')
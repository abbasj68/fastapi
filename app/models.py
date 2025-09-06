import datetime
from sqlalchemy import Column, Integer, String , DateTime, Text , ForeignKey ,Boolean ,Float
from sqlalchemy.orm import relationship
from pydantic import BaseModel, EmailStr
from .database import Base
from geoalchemy2 import Geometry

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
    deleted = Column(Boolean , default=False)
    
    is_superuser = Column(Boolean, default=False)

class TokenBlocklist(Base):
    __tablename__ = "token"
    __allow_unmapped__ = True

    id = Column(Integer,primary_key=True , index=True)
    token = Column(String(512), unique=True, nullable=False)
    jti = Column(String(36), unique=True, nullable=False)
    user_id = Column(Integer , ForeignKey("users.id"))
    created_at = Column(DateTime , default=datetime.datetime.utcnow)
    expires_at = Column(DateTime, nullable=True ,default=None )
    revoked = Column(Boolean , default=False)

    user = relationship('User', back_populates='tokens')
    
class Cafe(Base):
    __tablename__ = "cafes"
    __allow_unmapped__ = True
    
    id = Column(Integer , primary_key=True ,index=True)
    name = Column(String(150), nullable=False)
    address = Column(String(255), nullable=True)
    location = Column(Geometry(geometry_type="POINT", srid=4326))
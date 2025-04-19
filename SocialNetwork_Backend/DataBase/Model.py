from sqlalchemy import Column, Integer, String, Boolean, Text, TIMESTAMP, func
from database import Base


class User(Base):
    __tablename__ = "Users"

    UserId = Column(Integer, primary_key=True, index=True)
    Username = Column(String(255), nullable=False)
    Email = Column(String(255), nullable=False, unique=True)
    Hashed_Password = Column(String(255), nullable=False)
    Profile_Picture_Link = Column(Text, nullable=True)
    Created_At = Column(TIMESTAMP, server_default=func.now())
    Is_Private = Column(Boolean, default=False)

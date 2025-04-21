from sqlalchemy import Column, Integer, String, Boolean, Text, TIMESTAMP, func
from DataBase.database import Base


class User(Base):
    __tablename__ = "Users"

    userid = Column(Integer, primary_key=True, index=True, autoincrement=True)
    username = Column(String(255), nullable=False)
    email = Column(String(255), nullable=False, unique=True)
    hashed_password = Column(String(255), nullable=False)
    profile_picture_link = Column(Text, nullable=True)
    created_at = Column(TIMESTAMP, server_default=func.now())
    is_private = Column(Boolean, default=False)

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy import text


SQLALCHEMY_DATABASE_URL = "postgresql://postgres:Sana1382@localhost:5432/SocialNetwork"
engine = create_engine(SQLALCHEMY_DATABASE_URL)



SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

try:
    with engine.connect() as connection:
        result = connection.execute(text("SELECT 1"))
        print("__--__DataBase Connection Successful :) __--__")
except Exception as e:
    print("__--__DataBase Connection UnSuccessful :( __--__ ")
    print("Error:", e)
from passlib.context import CryptContext
from jose import jwt, JWTError
from datetime import datetime, timedelta
from dotenv import load_dotenv
import os

'''
In This File We Use Extra File To Put Critical JWT Information In It And Load It From Outside The Program For More
Safety And Secure... 
'''

load_dotenv()

SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = os.getenv("ALGORITHM")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 30))




PWD_context = CryptContext(schemes=["bcrypt"])

def GetHashedPassword(password: str):
    return PWD_context.hash(password)

def PasswordVerification(TruePassword: str, HashedPassword: str):
    return PWD_context.verify(TruePassword, HashedPassword)

def CreateToken(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + (timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def VerifyToken(token: str):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError as e:
        print("Tokken Is Invalid or Expired")
        print("Error :", e)
        return None

from pydantic import BaseModel,EmailStr
from typing import Optional



try:

   class UserRegister(BaseModel):
     Username: str
     Email: EmailStr
     Password: str
     Profile_Picture_Link: str | None = None
     Is_Private:bool

   class UserLogin(BaseModel):
       Email: EmailStr
       Password: str


   class Token(BaseModel):
       access_token: str
       token_type: str

except Exception as e:
    print("Error :",e)
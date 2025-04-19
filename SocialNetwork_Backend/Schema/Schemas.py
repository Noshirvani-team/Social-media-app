from pydantic import BaseModel,EmailStr
from typing import Optional



try:

   class UserRegister(BaseModel):
     UserName: str
     EmailStr: EmailStr
     Password: str
     Profile_Picture_Link: Optional[str] = None

   class UserLogin(BaseModel):
       EmailStr: EmailStr
       Password: str


   class Token(BaseModel):
       access_token: str
       token_type: str

except Exception as e:
    print("Error :",e)
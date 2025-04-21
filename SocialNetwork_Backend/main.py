from  fastapi import FastAPI, HTTPException,APIRouter,Depends
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from Schema import Model, Schemas
from DataBase.database import engine, get_db
from Schema.Hash_JWT import GetHashedPassword, PasswordVerification, CreateToken, VerifyToken

Model.Base.metadata.create_all(bind=engine)

app = FastAPI()
router = APIRouter()
TokenValdiation = OAuth2PasswordBearer(tokenUrl="/login")


@app.get("/")
def WelcomOage():
    return("___Website Is In Process___")






@router.post("/register")
def register(user: Schemas.UserRegister, db: Session = Depends(get_db)):
    db_user = db.query(Model.User).filter(Model.User.email == user.Email).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered. Please Enter a New Email")

    hashed_pw = GetHashedPassword(user.Password)

    CeatedUser = Model.User(
        username=user.Username,
        email=user.Email,
        hashed_password=hashed_pw,
        profile_picture_link=user.Profile_Picture_Link,
        is_private=user.Is_Private
    )
    db.add(CeatedUser)
    db.commit()
    db.refresh(CeatedUser)
    return {"msg": "User registered successfully"}







@router.post("/login", response_model=Schemas.Token)
def login(EnteredUser: Schemas.UserLogin, db: Session = Depends(get_db)):
    DB_user = db.query(Model.User).filter(Model.User.email == EnteredUser.Email).first()
    if not DB_user :
        raise HTTPException(status_code=401, detail="Invalid Information")
    if not PasswordVerification(EnteredUser.Password, DB_user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid password")

    token = CreateToken(data={"sub": DB_user.email})
    return {"access_token": token, "token_type": "bearer"}





@router.get("/protected")
def protected(token: str = Depends(TokenValdiation)):
    payload = VerifyToken(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    return {"msg": f"Authenticated as {payload['sub']}"}


app.include_router(router)

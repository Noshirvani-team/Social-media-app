from fastapi import FastAPI, HTTPException, APIRouter, Depends, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from Schema import Model, Schemas
from DataBase.database import engine, get_db
from Schema.Hash_JWT import GetHashedPassword, PasswordVerification, CreateToken, VerifyToken

Model.Base.metadata.create_all(bind=engine)

app = FastAPI()
router = APIRouter()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/login")


def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    payload = VerifyToken(token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    user = db.query(Model.User).filter(Model.User.email == payload.get("sub")).first()
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return user

def get_admin_user(current_user: Model.User = Depends(get_current_user)): #Just for admin
    if not getattr(current_user, "is_admin", False):
        raise HTTPException(status_code=403, detail="Only admins can access this route")
    return current_user

@app.get("/")
def WelcomePage():
    return {"msg": "___Website Is In Process___"}


@router.post("/register")
def register(user: Schemas.UserRegister, db: Session = Depends(get_db)):
    db_user = db.query(Model.User).filter(Model.User.email == user.Email).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")

    hashed_pw = GetHashedPassword(user.Password)
    created_user = Model.User(
        username=user.Username,
        email=user.Email,
        hashed_password=hashed_pw,
        profile_picture_link=user.Profile_Picture_Link,
        is_private=user.Is_Private
    )
    db.add(created_user)
    db.commit()
    db.refresh(created_user)
    return {"msg": "User registered successfully"}


@router.post("/login", response_model=Schemas.Token)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(Model.User).filter(Model.User.username == form_data.username).first()
    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    if not PasswordVerification(form_data.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid password")

    token = CreateToken(data={"sub": user.email})
    return {"access_token": token, "token_type": "bearer"}


@router.get("/protected") # For testing prtoextion
def protected(current_user: Model.User = Depends(get_current_user)):
    return {"msg": f"Authenticated as {current_user.email}"}


@router.get("/admin/panel") #just for admin panel...
def admin_panel(current_admin: Model.User = Depends(get_admin_user)):
    return {"msg": f"Welcome Admin: {current_admin.username}"}


@router.get("/user/me") # For testing prtoection...
def get_me(current_user: Model.User = Depends(get_current_user)):
    return {
        "username": current_user.username,
        "email": current_user.email,
        "private": current_user.is_private
    }

app.include_router(router)

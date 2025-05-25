from fastapi import FastAPI, HTTPException, APIRouter, Depends, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from Schema import Model, Schemas
from DataBase.database import engine, get_db
from Schema.Hash_JWT import GetHashedPassword, PasswordVerification, CreateToken, VerifyToken
from typing import List
from Schema.Schemas import PostCreate,PostOut
from Schema.Model import Post as PostModel, User as UserModel
import os
from fastapi import File, UploadFile, Form
from fastapi.staticfiles import StaticFiles



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


if not os.path.exists("media"):
    os.makedirs("media")
app.mount("/media", StaticFiles(directory="media"), name="media")









@app.get("/")
def WelcomePage():
    return {"msg": "___Website Is In Process___"}


# Router for Reg/Log         <<<<<<<<>>>>>>>


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


# Router for Posts      <<<<<<<<>>>>>>>>
@router.post("/post/create", response_model=PostOut)
def create_post(
    file: UploadFile = File(...),
    description: str = Form(""),
    is_published: bool = Form(True),
    db: Session = Depends(get_db),
    current_user: Model.User = Depends(get_current_user)
):
    try:
        filename = f"{current_user.userid}_{file.filename}"
        filepath = os.path.join("media", filename)
        with open(filepath, "wb") as buffer:
            buffer.write(file.file.read())

        new_post = PostModel(
            userid=current_user.userid,
            description=description,
            pic_video_link=f"/media/{filename}",
            is_published=is_published
        )
        db.add(new_post)
        db.commit()
        db.refresh(new_post)
        return new_post
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error creating post: {str(e)}")


@router.get("/post/my", response_model=List[PostOut])
def get_my_posts(
    db: Session = Depends(get_db),
    current_user: Model.User = Depends(get_current_user)
):
    try:
        posts = db.query(PostModel).filter(PostModel.userid == current_user.userid).all()
        return posts
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching your posts: {str(e)}")


@router.get("/post/public", response_model=List[PostOut])
def get_all_published_posts(db: Session = Depends(get_db)):
    try:
        posts = db.query(PostModel).filter(PostModel.is_published == True).all()
        return posts
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching public posts: {str(e)}")



@router.delete("/post/delete/{post_id}")
def delete_post(
    post_id: int,
    db: Session = Depends(get_db),
    current_user: Model.User = Depends(get_current_user)
):
    try:
        post = db.query(PostModel).filter(PostModel.postid == post_id).first()
        if not post:
            raise HTTPException(status_code=404, detail="Post not found")
        if post.userid != current_user.userid:
            raise HTTPException(status_code=403, detail="Unauthorized")

        # حذف فایل فیزیکی
        if post.pic_video_link and os.path.exists(post.pic_video_link[1:]):
            os.remove(post.pic_video_link[1:])

        db.delete(post)
        db.commit()
        return {"msg": "Post and file deleted successfully"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Delete failed: {str(e)}")


# Next Router       <<<<<<<<>>>>>>>>>>























#-----------------------It Was Just For Test------------------------
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

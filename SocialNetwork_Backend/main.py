from fastapi import FastAPI, HTTPException, APIRouter, Depends, status, File, UploadFile, Form
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from Schema import Model, Schemas
from DataBase.database import engine, get_db
from Schema.Hash_JWT import GetHashedPassword, PasswordVerification, CreateToken, VerifyToken
from DataBase.mongo_db import fs
from bson import ObjectId
from datetime import datetime
from DataBase.mongo_db import posts_collection
from fastapi.responses import StreamingResponse
from bson import ObjectId


Model.Base.metadata.create_all(bind=engine)

app = FastAPI()
core_router = APIRouter()
media_router = APIRouter(prefix="/media", tags=["Media"])

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

def get_admin_user(current_user: Model.User = Depends(get_current_user)):
    if not getattr(current_user, "is_admin", False):
        raise HTTPException(status_code=403, detail="Only admins can access this route")
    return current_user


@app.get("/")
def welcome_page():
    return {"msg": "___Website Is In Process___"}





#___________________________Reg/Log___________________________________
@core_router.post("/register")
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

@core_router.post("/login", response_model=Schemas.Token)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(Model.User).filter(Model.User.username == form_data.username).first()
    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    if not PasswordVerification(form_data.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid password")

    token = CreateToken(data={"sub": user.email})
    return {"access_token": token, "token_type": "bearer"}


#_____________________________Post_________________________

@media_router.post("/posts", response_model=dict)
async def create_post(
    file: UploadFile = File(...),
    description: str = Form(""),
    is_published: bool = Form(True),
    current_user: Model.User = Depends(get_current_user)
):
    contents = await file.read()
    file_id = fs.put(contents, filename=file.filename, content_type=file.content_type)

    post = {
        "userid": current_user.userid,
        "description": description,
        "pic_video_link": str(file_id),
        "created_at": datetime.utcnow(),
        "is_published": is_published
    }
    result = posts_collection.insert_one(post)
    return {"msg": "Post created", "post_id": str(result.inserted_id)}


@media_router.delete("/posts/{post_id}")
def delete_post(post_id: str, current_user: Model.User = Depends(get_current_user)):
    post = posts_collection.find_one({"_id": ObjectId(post_id)})

    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    if post["userid"] != current_user.userid:
        raise HTTPException(status_code=403, detail="Not authorized")

    if "pic_video_link" in post:
        fs.delete(ObjectId(post["pic_video_link"]))

    posts_collection.delete_one({"_id": ObjectId(post_id)})
    return {"msg": "Post deleted"}

@media_router.put("/posts/{post_id}")
def update_post(
    post_id: str,
    description: str = Form(None),
    is_published: bool = Form(None),
    current_user: Model.User = Depends(get_current_user)
):
    post = posts_collection.find_one({"_id": ObjectId(post_id)})
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    if post["userid"] != current_user.userid:
        raise HTTPException(status_code=403, detail="Not authorized")

    update_fields = {}
    if description is not None:
        update_fields["description"] = description
    if is_published is not None:
        update_fields["is_published"] = is_published

    posts_collection.update_one({"_id": ObjectId(post_id)}, {"$set": update_fields})
    return {"msg": "Post updated"}

@media_router.get("/posts/me", response_model=list[Schemas.MongoPostOut])
def get_my_posts(current_user: Model.User = Depends(get_current_user)):
    posts = posts_collection.find({"userid": current_user.userid})
    return [Schemas.MongoPostOut(
        postid=str(p["_id"]),
        userid=p["userid"],
        description=p.get("description"),
        pic_video_link=p.get("pic_video_link"),
        created_at=p["created_at"],
        is_published=p["is_published"]
    ) for p in posts]


@media_router.get("/posts/public", response_model=list[Schemas.MongoPostOut])
def get_public_posts():
    posts = posts_collection.find({"is_published": True})
    return [Schemas.MongoPostOut(
        postid=str(p["_id"]),
        userid=p["userid"],
        description=p.get("description"),
        pic_video_link=p.get("pic_video_link"),
        created_at=p["created_at"],
        is_published=p["is_published"]
    ) for p in posts]


@media_router.get("/media/{file_id}")
def get_media(file_id: str):
    try:
        file = fs.get(ObjectId(file_id))
        return StreamingResponse(file, media_type=file.content_type)
    except Exception:
        raise HTTPException(status_code=404, detail="File not found")


#_______________________________Next Rout_______________________________

#For Authentication
@core_router.get("/protected")
def protected(current_user: Model.User = Depends(get_current_user)):
    return {"msg": f"Authenticated as {current_user.email}"}

@core_router.get("/admin/panel")
def admin_panel(current_admin: Model.User = Depends(get_admin_user)):
    return {"msg": f"Welcome Admin: {current_admin.username}"}

@core_router.get("/user/me")
def get_me(current_user: Model.User = Depends(get_current_user)):
    return {
        "username": current_user.username,
        "email": current_user.email,
        "private": current_user.is_private
    }



app.include_router(core_router)
app.include_router(media_router)

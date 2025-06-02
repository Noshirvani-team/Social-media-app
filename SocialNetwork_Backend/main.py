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
from Schema.Model import Comment
from Schema.Schemas import CommentOut,CommentCreate
from io import BytesIO


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
    db: Session = Depends(get_db),
    current_user: Model.User = Depends(get_current_user)
):
    contents = await file.read()
    file_id = fs.put(contents, filename=file.filename, content_type=file.content_type)

    new_post = Model.Post(
        userid=current_user.userid,
        description=description,
        pic_video_link=str(file_id),
        is_published=is_published
    )
    db.add(new_post)
    db.commit()
    db.refresh(new_post)
    return {"msg": "Post created", "post_id": new_post.postid}


@media_router.delete("/posts/{post_id}")
def delete_post(post_id: int, current_user: Model.User = Depends(get_current_user), db: Session = Depends(get_db)):
    post = db.query(Model.Post).filter(Model.Post.postid == post_id).first()

    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    if post.userid != current_user.userid:
        raise HTTPException(status_code=403, detail="Not authorized")

    if post.pic_video_link:
        try:
            fs.delete(ObjectId(post.pic_video_link))
        except:
            pass

    db.delete(post)
    db.commit()
    return {"msg": "Post deleted"}

@media_router.put("/posts/{post_id}")
def update_post(
    post_id: int,
    description: str = Form(None),
    is_published: bool = Form(None),
    db: Session = Depends(get_db),
    current_user: Model.User = Depends(get_current_user)
):
    post = db.query(Model.Post).filter(Model.Post.postid == post_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    if post.userid != current_user.userid:
        raise HTTPException(status_code=403, detail="Not authorized")

    if description is not None:
        post.description = description
    if is_published is not None:
        post.is_published = is_published

    db.commit()
    db.refresh(post)
    return {"msg": "Post updated"}


@media_router.get("/posts/me", response_model=list[Schemas.MongoPostOut])
def get_my_posts(current_user: Model.User = Depends(get_current_user), db: Session = Depends(get_db)):
    posts = db.query(Model.Post).filter(Model.Post.userid == current_user.userid).all()
    return [
        Schemas.MongoPostOut(
            postid=str(p.postid),
            userid=p.userid,
            description=p.description,
            pic_video_link=f"/media/{p.pic_video_link}",
            created_at=p.created_at,
            is_published=p.is_published
        ) for p in posts
    ]


@media_router.get("/posts/public", response_model=list[Schemas.MongoPostOut])
def get_public_posts(db: Session = Depends(get_db)):
    posts = db.query(Model.Post).filter(Model.Post.is_published == True).order_by(Model.Post.created_at.desc()).all()
    return [
        Schemas.MongoPostOut(
            postid=str(p.postid),
            userid=p.userid,
            description=p.description,
            pic_video_link=f"/media/{p.pic_video_link}",  # مسیر دستیابی به فایل در GridFS
            created_at=p.created_at,
            is_published=p.is_published
        ) for p in posts
    ]


@media_router.get("/media/{file_id}")
def get_media(file_id: str):
    try:
        file = fs.get(ObjectId(file_id))

        media_type = file.content_type

        headers = {"Content-Disposition": f"inline; filename={file.filename}"}
        return StreamingResponse(BytesIO(file.read()), media_type=media_type, headers=headers)

    except Exception as e:
        print(f"Error: {e}")
        raise HTTPException(status_code=404, detail="File not found")


#_______________________________Comments_______________________________
@core_router.post("/comments", response_model=CommentOut)
def create_comment(
    comment: CommentCreate,
    db: Session = Depends(get_db),
    current_user: Model.User = Depends(get_current_user)
):
    new_comment = Comment(
        userid=current_user.userid,
        postid=comment.PostId,
        context=comment.Context
    )
    db.add(new_comment)
    db.commit()
    db.refresh(new_comment)
    return CommentOut(
        CommentId=new_comment.commentid,
        UserId=new_comment.userid,
        PostId=new_comment.postid,
        Context=new_comment.context,
        Created_At=str(new_comment.created_at)
    )


@core_router.get("/comments/{post_id}", response_model=list[CommentOut])
def get_comments_for_post(post_id: int, db: Session = Depends(get_db)):
    comments = db.query(Comment).filter(Comment.postid == post_id).order_by(Comment.created_at.desc()).all()
    return [
        CommentOut(
            CommentId=c.commentid,
            UserId=c.userid,
            PostId=c.postid,
            Context=c.context,
            Created_At=str(c.created_at)
        ) for c in comments
    ]


@core_router.delete("/comments/{comment_id}")
def delete_comment(
        comment_id: int,
        db: Session = Depends(get_db),
        current_user: Model.User = Depends(get_current_user)
):
    comment = db.query(Comment).filter(Comment.commentid == comment_id).first()
    if not comment:
        raise HTTPException(status_code=404, detail="Comment not found")
    if comment.userid != current_user.userid and not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Not authorized to delete this comment")

    db.delete(comment)
    db.commit()
    return {"msg": "Comment deleted"}
#_______________________________Likes_______________________________
@media_router.post("/likes", response_model=Schemas.LikeOut)
def create_like(
        like: Schemas.LikeCreate,
        db: Session = Depends(get_db),
        current_user: Model.User = Depends(get_current_user)
):
    existing_like = db.query(Model.Like).filter(
        Model.Like.userid == current_user.userid,
        Model.Like.postid == like.PostId
    ).first()

    if existing_like:
        raise HTTPException(status_code=400, detail="Post already liked")

    new_like = Model.Like(userid=current_user.userid, postid=like.PostId)
    db.add(new_like)
    db.commit()
    db.refresh(new_like)
    return Schemas.LikeOut(LikeId=new_like.likeid, UserId=new_like.userid, PostId=new_like.postid)


@media_router.delete("/likes/{like_id}")
def delete_like(
        like_id: int,
        db: Session = Depends(get_db),
        current_user: Model.User = Depends(get_current_user)
):
    like = db.query(Model.Like).filter(Model.Like.likeid == like_id).first()
    if not like:
        raise HTTPException(status_code=404, detail="Like not found")

    if like.userid != current_user.userid:
        raise HTTPException(status_code=403, detail="Not authorized to delete this like")

    db.delete(like)
    db.commit()
    return {"msg": "Like deleted"}


@media_router.get("/likes/post/{post_id}", response_model=int)
def get_likes_count_for_post(
        post_id: int,
        db: Session = Depends(get_db)
):
    likes_count = db.query(Model.Like).filter(Model.Like.postid == post_id).count()
    return likes_count


@media_router.get("/likes/user/{user_id}", response_model=int)
def get_likes_count_for_user(
        user_id: int,
        db: Session = Depends(get_db)
):
    likes_count = db.query(Model.Like).filter(Model.Like.userid == user_id).count()
    return likes_count

#_______________________________Following_______________________________
@core_router.post("/follow", response_model=Schemas.FollowerOut)
def follow_user(
    follow: Schemas.FollowAction,
    db: Session = Depends(get_db),
    current_user: Model.User = Depends(get_current_user)
):
    if current_user.userid == follow.FollowingId:
        raise HTTPException(status_code=400, detail="You cannot follow yourself")

    existing = db.query(Model.Follower).filter(
        Model.Follower.followerid == current_user.userid,
        Model.Follower.followingid == follow.FollowingId
    ).first()

    if existing:
        raise HTTPException(status_code=400, detail="Already following")

    new_follow = Model.Follower(followerid=current_user.userid, followingid=follow.FollowingId)
    db.add(new_follow)
    db.commit()
    db.refresh(new_follow)
    return Schemas.FollowerOut(
        FollowerId=new_follow.followerid,
        FollowingId=new_follow.followingid,
        Followed_At=str(new_follow.followed_at)
    )

@core_router.delete("/unfollow/{following_id}")
def unfollow_user(
    following_id: int,
    db: Session = Depends(get_db),
    current_user: Model.User = Depends(get_current_user)
):
    follow = db.query(Model.Follower).filter(
        Model.Follower.followerid == current_user.userid,
        Model.Follower.followingid == following_id
    ).first()

    if not follow:
        raise HTTPException(status_code=404, detail="Not following this user")

    db.delete(follow)
    db.commit()
    return {"msg": "Unfollowed"}

@core_router.get("/followers/{user_id}", response_model=list[Schemas.FollowerOut])
def get_followers(user_id: int, db: Session = Depends(get_db)):
    followers = db.query(Model.Follower).filter(Model.Follower.followingid == user_id).all()
    return [
        Schemas.FollowerOut(
            FollowerId=f.followerid,
            FollowingId=f.followingid,
            Followed_At=str(f.followed_at)
        ) for f in followers
    ]


@core_router.get("/following/{user_id}", response_model=list[Schemas.FollowerOut])
def get_following(user_id: int, db: Session = Depends(get_db)):
    following = db.query(Model.Follower).filter(Model.Follower.followerid == user_id).all()
    return [
        Schemas.FollowerOut(
            FollowerId=f.followerid,
            FollowingId=f.followingid,
            Followed_At=str(f.followed_at)
        ) for f in following
    ]

@core_router.get("/follower/count/{user_id}", response_model=int)
def count_followers(user_id: int, db: Session = Depends(get_db)):
    count = db.query(Model.Follower).filter(Model.Follower.followingid == user_id).count()
    return count

@core_router.get("/following/count/{user_id}", response_model=int)
def count_following(user_id: int, db: Session = Depends(get_db)):
    count = db.query(Model.Follower).filter(Model.Follower.followerid == user_id).count()
    return count

#__________________________Next Rout___________________________________


#__________________________For Authentication___________________________
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

from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime
try:

    #  User Schemas<<<<<>>>>>>

    class UserRegister(BaseModel):
        Username: str
        Email: EmailStr
        Password: str
        Profile_Picture_Link: Optional[str] = None
        Is_Private: bool

    class UserLogin(BaseModel):
        Email: EmailStr
        Password: str

    class Token(BaseModel):
        access_token: str
        token_type: str

    # Post Schemas    <<<<<>>>>>

    class PostCreate(BaseModel):
        Description: Optional[str] = None
        Pic_Video_Link: Optional[str] = None
        Is_Published: Optional[bool] = True


    class PostOut(BaseModel):
        postid: int
        userid: int
        description: Optional[str]
        pic_video_link: Optional[str]
        created_at: datetime
        is_published: bool

        class Config:
            from_attributes = True


    #Comment Schemas <<<<<<<>>>>>>>

    class CommentCreate(BaseModel):
        PostId: int
        Context: str

    class CommentOut(BaseModel):
        CommentId: int
        UserId: int
        PostId: int
        Context: str
        Created_At: str

        class Config:
            from_attributes = True

    #Like Schemas<<<<<<<<>>>>>>>>

    class LikeCreate(BaseModel):
        PostId: int

    class LikeOut(BaseModel):
        LikeId: int
        UserId: int
        PostId: int

        class Config:
            from_attributes = True

    #Notification Schemas <<<<<<<<< >>>>>>>>>

    class NotificationOut(BaseModel):
        NotifId: int
        UserId: int
        Type: Optional[str]
        PostLink: Optional[str]

        class Config:
            from_attributes = True

    #Follower Schemas <<<<<<<<>>>>>>>>

    class FollowAction(BaseModel):
        FollowingId: int

    class FollowerOut(BaseModel):
        FollowerId: int
        FollowingId: int
        Followed_At: str

        class Config:
            from_attributes = True

except Exception as e:
    print("Error:", e)

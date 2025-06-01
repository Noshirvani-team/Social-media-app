from sqlalchemy import Column, Integer, String, Boolean, Text, TIMESTAMP, func
from DataBase.database import Base
from sqlalchemy import PrimaryKeyConstraint
from sqlalchemy import ForeignKey
from sqlalchemy.orm import relationship



class User(Base):
    __tablename__ = "Users"
    userid = Column(Integer, primary_key=True, index=True, autoincrement=True)
    username = Column(String(255), nullable=False)
    email = Column(String(255), nullable=False, unique=True)
    hashed_password = Column(String(255), nullable=False)
    profile_picture_link = Column(Text, nullable=True)
    created_at = Column(TIMESTAMP, server_default=func.now())
    is_private = Column(Boolean, default=False)
    likes = relationship("Like", back_populates="user")


class Post(Base):
    __tablename__ = "Post"

    postid = Column(Integer, primary_key=True, index=True, autoincrement=True)
    userid = Column(Integer, nullable=False)
    description = Column(Text, nullable=True)
    pic_video_link = Column(Text, nullable=True)
    created_at = Column(TIMESTAMP, server_default=func.now())
    is_published = Column(Boolean, default=True)
    likes = relationship("Like", back_populates="post")

class Comment(Base):
    __tablename__ = "Comment"
    commentid = Column(Integer, primary_key=True, index=True, autoincrement=True)
    userid = Column(Integer, nullable=False)
    postid = Column(Integer, ForeignKey('Post.postid'), nullable=False)
    context = Column(Text, nullable=False)
    created_at = Column(TIMESTAMP, server_default=func.now())


class Like(Base):
    __tablename__ = "Likes"

    likeid = Column(Integer, primary_key=True, index=True, autoincrement=True)
    userid = Column(Integer, ForeignKey('Users.userid'), nullable=False)
    postid = Column(Integer, ForeignKey('Post.postid'), nullable=False)

    user = relationship("User", back_populates="likes")
    post = relationship("Post", back_populates="likes")


class Notification(Base):
    __tablename__ = "Notification"
    notifid = Column(Integer, primary_key=True, index=True, autoincrement=True)
    userid = Column(Integer, nullable=False)
    type = Column(String(100))
    postlink = Column(Text, nullable=True)

class Follower(Base):
    __tablename__ = "Follower"
    followerid = Column(Integer, primary_key=False)
    followingid = Column(Integer, primary_key=False)
    followed_at = Column(TIMESTAMP, server_default=func.now())
    __table_args__ = (
        PrimaryKeyConstraint('followerid', 'followingid'),
    )

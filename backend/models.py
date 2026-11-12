from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime
from database import Base


class Agent(Base):
    __tablename__ = "agents"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    company = Column(String(100), nullable=False)
    description = Column(Text, nullable=False)
    interests = Column(Text, nullable=False)  # comma-separated
    avatar_color = Column(String(20), default="#6c63ff")
    created_at = Column(DateTime, default=datetime.utcnow)

    posts = relationship("Post", back_populates="author", foreign_keys="Post.agent_id")
    comments = relationship("Comment", back_populates="author")
    notifications = relationship("Notification", back_populates="agent", foreign_keys="Notification.agent_id")


class Post(Base):
    __tablename__ = "posts"

    id = Column(Integer, primary_key=True, index=True)
    content = Column(Text, nullable=False)
    agent_id = Column(Integer, ForeignKey("agents.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    author = relationship("Agent", back_populates="posts", foreign_keys=[agent_id])
    comments = relationship("Comment", back_populates="post", cascade="all, delete-orphan")
    notifications = relationship("Notification", back_populates="post", cascade="all, delete-orphan")


class Comment(Base):
    __tablename__ = "comments"

    id = Column(Integer, primary_key=True, index=True)
    content = Column(Text, nullable=False)
    post_id = Column(Integer, ForeignKey("posts.id"), nullable=False)
    agent_id = Column(Integer, ForeignKey("agents.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    post = relationship("Post", back_populates="comments")
    author = relationship("Agent", back_populates="comments")


class Notification(Base):
    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True, index=True)
    agent_id = Column(Integer, ForeignKey("agents.id"), nullable=False)   # recipient
    post_id = Column(Integer, ForeignKey("posts.id"), nullable=False)
    score = Column(String(20), default="0.0")
    read = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    agent = relationship("Agent", back_populates="notifications", foreign_keys=[agent_id])
    post = relationship("Post", back_populates="notifications")

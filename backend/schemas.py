from pydantic import BaseModel, ConfigDict
from datetime import datetime
from typing import Optional, List


# ── Agent ────────────────────────────────────────────────────────────────────

class AgentCreate(BaseModel):
    name: str
    company: str
    description: str
    interests: str          # comma-separated string
    avatar_color: Optional[str] = "#6c63ff"


class AgentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    company: str
    description: str
    interests: str
    avatar_color: str
    created_at: datetime


# ── Comment ──────────────────────────────────────────────────────────────────

class CommentCreate(BaseModel):
    agent_id: int
    content: str


class CommentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    content: str
    post_id: int
    agent_id: int
    created_at: datetime
    author: Optional[AgentOut] = None


# ── Post ─────────────────────────────────────────────────────────────────────

class PostCreate(BaseModel):
    agent_id: int
    content: str


class NotifiedAgentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    company: str
    score: float


class PostOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    content: str
    agent_id: int
    created_at: datetime
    author: Optional[AgentOut] = None
    comments: List[CommentOut] = []
    notification_count: int = 0


class PostCreateResponse(BaseModel):
    post: PostOut
    notified_agents: List[NotifiedAgentOut]


# ── Notification ──────────────────────────────────────────────────────────────

class NotificationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    agent_id: int
    post_id: int
    score: str
    read: bool
    created_at: datetime
    post: Optional[PostOut] = None


# ── Feed ─────────────────────────────────────────────────────────────────────

class FeedPostOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    content: str
    agent_id: int
    created_at: datetime
    author: Optional[AgentOut] = None
    comments: List[CommentOut] = []
    notification_count: int = 0
    notified_agents: List[AgentOut] = []


# ── Stats ─────────────────────────────────────────────────────────────────────

class StatsOut(BaseModel):
    total_agents: int
    total_posts: int
    total_notifications: int

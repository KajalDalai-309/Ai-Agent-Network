"""
main.py – FastAPI application entry point
"""

from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session, joinedload

import models
import schemas
from database import Base, engine, get_db, SessionLocal
from routing_engine import SEED_AGENTS

# ── Lifespan (startup / shutdown) ─────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Create tables
    Base.metadata.create_all(bind=engine)

    # Seed demo agents if DB is empty
    db: Session = SessionLocal()
    try:
        count = db.query(models.Agent).count()
        if count == 0:
            for sa in SEED_AGENTS:
                agent = models.Agent(**sa)
                db.add(agent)
            db.commit()
            print(f"[startup] Seeded {len(SEED_AGENTS)} demo agents.")
        else:
            print(f"[startup] DB already has {count} agents – skipping seed.")
    finally:
        db.close()

    yield  # app runs


# ── App ────────────────────────────────────────────────────────────────────────

app = FastAPI(
    title="AgentNet API",
    description="Social Network for AI Agents – backend",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS - Allow local and deployed frontends (e.g. Render, Vercel)
app.add_middleware(
    CORSMiddleware,
    allow_origin_regex=r"^https?://.*",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Routers ───────────────────────────────────────────────────────────────────

from router.agents import router as agents_router
from router.posts import router as posts_router
from router.comments import router as comments_router
from router.routing import router as routing_router

app.include_router(agents_router)
app.include_router(posts_router)
app.include_router(comments_router)
app.include_router(routing_router)


# ── Feed endpoint ─────────────────────────────────────────────────────────────

@app.get("/api/v1/feed", response_model=list[schemas.FeedPostOut], tags=["feed"])
def get_feed(skip: int = 0, limit: int = 50, db: Session = Depends(get_db)):
    """
    Return all posts (newest first) with author, comments, notification count,
    and the list of notified agents.
    """
    posts = (
        db.query(models.Post)
        .options(
            joinedload(models.Post.author),
            joinedload(models.Post.comments).joinedload(models.Comment.author),
            joinedload(models.Post.notifications).joinedload(models.Notification.agent),
        )
        .order_by(models.Post.created_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )

    feed = []
    for post in posts:
        notified_agents = [n.agent for n in post.notifications if n.agent]
        feed.append(
            schemas.FeedPostOut(
                id=post.id,
                content=post.content,
                agent_id=post.agent_id,
                created_at=post.created_at,
                author=post.author,
                comments=post.comments,
                notification_count=len(post.notifications),
                notified_agents=notified_agents,
            )
        )
    return feed


# ── Stats endpoint ─────────────────────────────────────────────────────────────

@app.get("/api/v1/stats", response_model=schemas.StatsOut, tags=["stats"])
def get_stats(db: Session = Depends(get_db)):
    return schemas.StatsOut(
        total_agents=db.query(models.Agent).count(),
        total_posts=db.query(models.Post).count(),
        total_notifications=db.query(models.Notification).count(),
    )


# ── Health ────────────────────────────────────────────────────────────────────

@app.get("/health", tags=["health"])
def health():
    return {"status": "ok", "service": "AgentNet API"}


# ── Dev runner ────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload
from typing import List

import models
import schemas
from database import get_db
from routing_engine import routing_engine

router = APIRouter(prefix="/api/v1/posts", tags=["posts"])


def _notification_count(post: models.Post) -> int:
    return len(post.notifications)


def _post_to_out(post: models.Post) -> schemas.PostOut:
    return schemas.PostOut(
        id=post.id,
        content=post.content,
        agent_id=post.agent_id,
        created_at=post.created_at,
        author=post.author,
        comments=post.comments,
        notification_count=_notification_count(post),
    )


@router.post("", response_model=schemas.PostCreateResponse, status_code=201)
def create_post(payload: schemas.PostCreate, db: Session = Depends(get_db)):
    """Create a post and trigger semantic routing to notify relevant agents."""
    agent = db.query(models.Agent).filter(models.Agent.id == payload.agent_id).first()
    if not agent:
        raise HTTPException(status_code=404, detail="Posting agent not found")

    # Persist post
    post = models.Post(content=payload.content, agent_id=payload.agent_id)
    db.add(post)
    db.commit()
    db.refresh(post)

    # Run routing engine
    all_agents = db.query(models.Agent).all()
    agent_dicts = [
        {
            "id": a.id,
            "name": a.name,
            "company": a.company,
            "description": a.description,
            "interests": a.interests,
        }
        for a in all_agents
    ]

    matches = routing_engine.route(
        post_content=payload.content,
        agents=agent_dicts,
        posting_agent_id=payload.agent_id,
    )

    notified: List[schemas.NotifiedAgentOut] = []
    for agent_id, name, company, score in matches:
        notif = models.Notification(
            agent_id=agent_id,
            post_id=post.id,
            score=str(round(score, 4)),
        )
        db.add(notif)
        notified.append(
            schemas.NotifiedAgentOut(id=agent_id, name=name, company=company, score=score)
        )

    db.commit()

    # Reload with relationships
    post = (
        db.query(models.Post)
        .options(
            joinedload(models.Post.author),
            joinedload(models.Post.comments).joinedload(models.Comment.author),
            joinedload(models.Post.notifications),
        )
        .filter(models.Post.id == post.id)
        .first()
    )

    return schemas.PostCreateResponse(post=_post_to_out(post), notified_agents=notified)


@router.get("", response_model=List[schemas.PostOut])
def list_posts(skip: int = 0, limit: int = 50, db: Session = Depends(get_db)):
    posts = (
        db.query(models.Post)
        .options(
            joinedload(models.Post.author),
            joinedload(models.Post.comments).joinedload(models.Comment.author),
            joinedload(models.Post.notifications),
        )
        .order_by(models.Post.created_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )
    return [_post_to_out(p) for p in posts]


@router.get("/{post_id}", response_model=schemas.PostOut)
def get_post(post_id: int, db: Session = Depends(get_db)):
    post = (
        db.query(models.Post)
        .options(
            joinedload(models.Post.author),
            joinedload(models.Post.comments).joinedload(models.Comment.author),
            joinedload(models.Post.notifications),
        )
        .filter(models.Post.id == post_id)
        .first()
    )
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    return _post_to_out(post)

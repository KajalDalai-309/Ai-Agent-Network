from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload

import models
import schemas
from database import get_db

router = APIRouter(prefix="/api/v1/posts", tags=["comments"])


@router.post("/{post_id}/comments", response_model=schemas.CommentOut, status_code=201)
def add_comment(
    post_id: int,
    payload: schemas.CommentCreate,
    db: Session = Depends(get_db),
):
    """Add a manual comment/reply to a post."""
    post = db.query(models.Post).filter(models.Post.id == post_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")

    agent = db.query(models.Agent).filter(models.Agent.id == payload.agent_id).first()
    if not agent:
        raise HTTPException(status_code=404, detail="Commenting agent not found")

    comment = models.Comment(
        content=payload.content,
        post_id=post_id,
        agent_id=payload.agent_id,
    )
    db.add(comment)
    db.commit()
    db.refresh(comment)

    comment = (
        db.query(models.Comment)
        .options(joinedload(models.Comment.author))
        .filter(models.Comment.id == comment.id)
        .first()
    )
    return comment


@router.post("/{post_id}/auto-respond", status_code=200)
def auto_respond(post_id: int, db: Session = Depends(get_db)):
    """
    Autonomous Agent Response Simulator (Assignment Step 3):
    Each notified agent receives the post event and autonomously uses LLM/persona
    to draft and post a relevant comment.
    """
    post = (
        db.query(models.Post)
        .options(
            joinedload(models.Post.author),
            joinedload(models.Post.notifications).joinedload(models.Notification.agent),
        )
        .filter(models.Post.id == post_id)
        .first()
    )
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")

    notified_agents = [n.agent for n in post.notifications if n.agent]
    if not notified_agents:
        return {"message": "No notified agents found for this post.", "comments_added": 0}

    responses_created = []
    author_name = post.author.company if post.author else "partner"

    for agent in notified_agents:
        already_commented = (
            db.query(models.Comment)
            .filter(models.Comment.post_id == post_id, models.Comment.agent_id == agent.id)
            .first()
        )
        if already_commented:
            continue

        comp = agent.company.lower()
        if "phonepe" in comp:
            text = f"Extra ₹50 cashback when you pay for {author_name} orders using PhonePe UPI!"
        elif "flipkart" in comp:
            text = f"Exclusive deal: Get 10% Flipkart SuperCoins on all {author_name} festive bookings."
        elif "hdfc" in comp:
            text = f"HDFC Bank cardholders get 10% instant discount up to ₹150 on {author_name} transactions."
        elif "swiggy" in comp:
            text = f"Swiggy Dineout pass unlocked with {author_name} offers this festive week!"
        elif "bajaj" in comp:
            text = f"Special corporate partner discount on Bajaj Chetak EV bookings for {author_name} users."
        else:
            text = f"Autonomous update from {agent.name}: Acknowledged post from {author_name}. Initiating automated partnership flow."

        new_comment = models.Comment(content=text, post_id=post_id, agent_id=agent.id)
        db.add(new_comment)
        responses_created.append({"agent": agent.name, "comment": text})

    db.commit()
    return {"message": f"{len(responses_created)} autonomous response(s) posted.", "responses": responses_created}


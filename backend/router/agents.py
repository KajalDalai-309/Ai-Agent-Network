from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

import models
import schemas
from database import get_db

router = APIRouter(prefix="/api/v1/agents", tags=["agents"])


@router.get("", response_model=List[schemas.AgentOut])
def list_agents(db: Session = Depends(get_db)):
    """Return all registered agents."""
    return db.query(models.Agent).order_by(models.Agent.created_at.desc()).all()


@router.get("/{agent_id}", response_model=schemas.AgentOut)
def get_agent(agent_id: int, db: Session = Depends(get_db)):
    agent = db.query(models.Agent).filter(models.Agent.id == agent_id).first()
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    return agent


@router.post("", response_model=schemas.AgentOut, status_code=201)
def create_agent(payload: schemas.AgentCreate, db: Session = Depends(get_db)):
    """Register a new AI agent."""
    agent = models.Agent(
        name=payload.name,
        company=payload.company,
        description=payload.description,
        interests=payload.interests,
        avatar_color=payload.avatar_color or "#6c63ff",
    )
    db.add(agent)
    db.commit()
    db.refresh(agent)
    return agent


@router.get("/{agent_id}/notifications", response_model=List[schemas.NotificationOut])
def get_notifications(agent_id: int, db: Session = Depends(get_db)):
    """Get all notifications for an agent."""
    agent = db.query(models.Agent).filter(models.Agent.id == agent_id).first()
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")

    notifications = (
        db.query(models.Notification)
        .filter(models.Notification.agent_id == agent_id)
        .order_by(models.Notification.created_at.desc())
        .all()
    )
    return notifications

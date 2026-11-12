"""
router/routing.py
─────────────────
Exposes the routing engine as a standalone endpoint so the frontend
can preview which agents would be notified for arbitrary text without
actually creating a post.
"""

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session
from typing import List

import models
import schemas
from database import get_db
from routing_engine import routing_engine

router = APIRouter(prefix="/api/v1/routing", tags=["routing"])


class RoutingPreviewRequest(BaseModel):
    content: str
    posting_agent_id: int


@router.post("/preview", response_model=List[schemas.NotifiedAgentOut])
def preview_routing(payload: RoutingPreviewRequest, db: Session = Depends(get_db)):
    """
    Dry-run the routing engine: return matched agents without persisting
    anything to the database.
    """
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
        posting_agent_id=payload.posting_agent_id,
    )

    return [
        schemas.NotifiedAgentOut(id=aid, name=name, company=company, score=score)
        for aid, name, company, score in matches
    ]

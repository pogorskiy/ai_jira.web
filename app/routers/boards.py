from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from .. import schemas, models
from ..database import get_session
from ..services.jira import JiraClient

router = APIRouter()

@router.get("/{board_id}/sprints", response_model=List[schemas.SprintOut])
async def get_sprints(board_id: int, refresh: bool = False, session: AsyncSession = Depends(get_session)):
    """
    Get sprints for a board. If refresh is False and cache exists, return cached sprints.
    Otherwise, fetch from Jira and update cache.
    """
    # Query cached sprints from database
    result = await session.execute(select(models.Sprint).where(models.Sprint.board_id == board_id))
    cached = result.scalars().all()

    if cached and not refresh:
        return [schemas.SprintOut.model_validate(sp) for sp in cached]

    client = JiraClient()
    try:
        sprints_raw = await client.list_sprints(board_id)
    except Exception as e:
        raise HTTPException(502, f"Failed to fetch sprints from Jira: {e}")

    for sp in sprints_raw:
        res = await session.execute(select(models.Sprint).where(models.Sprint.jira_id == sp["id"]))
        obj = res.scalar_one_or_none()
        if obj is None:
            # Create new sprint if not exists
            obj = models.Sprint(jira_id=sp["id"], board_id=board_id)
            obj.name = sp["name"]
            obj.state = sp.get("state", "")
            session.add(obj)
        else:
            # Update existing sprint fields
            obj.name = sp["name"]
            obj.state = sp.get("state", "")
    await session.commit()

    # Return up-to-date sprints from database
    result = await session.execute(select(models.Sprint).where(models.Sprint.board_id == board_id))
    updated = result.scalars().all()
    return [schemas.SprintOut.model_validate(sp) for sp in updated]
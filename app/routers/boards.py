from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from .. import schemas, models
from ..database import get_session
from ..services.jira import JiraClient

router = APIRouter()

@router.get("/{board_id}/sprints", response_model=List[schemas.SprintOut])
async def get_sprints(board_id: int, refresh: bool = False, session: AsyncSession = Depends(get_session)):
    result = await session.execute(select(models.Sprint).where(models.Sprint.board_id == board_id))
    cached = result.scalars().all()

    if cached and not refresh:
        return [schemas.SprintOut.model_validate(sp) for sp in cached]

    client = JiraClient()
    sprints_raw = await client.list_sprints(board_id)

    for sp in sprints_raw:
        res = await session.execute(select(models.Sprint).where(models.Sprint.jira_id == sp["id"]))
        obj = res.scalar_one_or_none()
        if obj is None:
            obj = models.Sprint(jira_id=sp["id"], board_id=board_id)
        obj.name = sp["name"]
        obj.state = sp.get("state", "")
        session.add(obj)
    await session.commit()

    return [schemas.SprintOut(jira_id=sp["id"], name=sp["name"], state=sp.get("state", "")) for sp in sprints_raw]
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from .. import schemas, models
from ..database import get_session
from ..services.jira import JiraClient

router = APIRouter()


@router.get("/{board_id}/sprints", response_model=List[schemas.SprintOut])
async def get_sprints(board_id: int, refresh: bool = False, session: AsyncSession = Depends(get_session)):
    # Check cache first unless refresh flag is set
    q = await session.execute(models.Sprint.__table__.select().where(models.Sprint.board_id == board_id))
    cached = q.fetchall()
    if cached and not refresh:
        # Pydantic v2 — use model_validate instead of deprecated from_orm
        return [schemas.SprintOut.model_validate(row) for row in cached]

    # Fetch from Jira
    client = JiraClient()
    sprints_raw = await client.list_sprints(board_id)

    # Upsert cache
    for sp in sprints_raw:
        obj = await session.scalar(models.Sprint.__table__.select().where(models.Sprint.jira_id == sp["id"]))
        if obj is None:
            obj = models.Sprint(jira_id=sp["id"], board_id=board_id)
        obj.name = sp["name"]
        obj.state = sp.get("state", "")
        session.add(obj)
    await session.commit()

    return [schemas.SprintOut(jira_id=sp["id"], name=sp["name"], state=sp.get("state", "")) for sp in sprints_raw]
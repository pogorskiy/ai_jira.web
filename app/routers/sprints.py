from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from .. import schemas, models
from ..database import get_session
from ..services.jira import JiraClient

router = APIRouter()


@router.get("/{sprint_id}/issues", response_model=schemas.SprintWithIssues)
async def get_issues_for_sprint(sprint_id: int, refresh: bool = False, session: AsyncSession = Depends(get_session)):
    sprint_row = await session.scalar(models.Sprint.__table__.select().where(models.Sprint.jira_id == sprint_id))

    if sprint_row and not refresh:
        issues_q = await session.execute(models.Issue.__table__.select().where(models.Issue.sprint_id == sprint_row.id))
        issues = issues_q.fetchall()
        return schemas.SprintWithIssues.model_validate({
            "jira_id": sprint_row.jira_id,
            "name": sprint_row.name,
            "state": sprint_row.state,
            "issues": [schemas.IssueOut.model_validate(dict(i)) for i in issues],
        })

    if not sprint_row and not refresh:
        raise HTTPException(status_code=404, detail="Sprint not cached; try refresh=true")

    # Fetch fresh data from Jira
    client = JiraClient()
    issues_raw = await client.list_issues_for_sprint(sprint_id)

    # Upsert sprint stub if it does not exist
    if sprint_row is None:
        sprint_row = models.Sprint(jira_id=sprint_id, name=f"Sprint {sprint_id}", board_id=0, state="unknown")
        session.add(sprint_row)
        await session.commit()

    # Clear and insert issues
    await session.execute(models.Issue.__table__.delete().where(models.Issue.sprint_id == sprint_row.id))
    for it in issues_raw:
        f = it["fields"]
        issue = models.Issue(
            jira_key=it["key"],
            summary=f.get("summary", ""),
            description=f.get("description"),
            is_subtask=f.get("issuetype", {}).get("subtask", False),
            parent_key=f.get("parent", {}).get("key"),
            sprint_id=sprint_row.id,
        )
        session.add(issue)
    await session.commit()

    # Return freshly validated response
    issues_q = await session.execute(models.Issue.__table__.select().where(models.Issue.sprint_id == sprint_row.id))
    issues = issues_q.fetchall()

    return schemas.SprintWithIssues.model_validate({
        "jira_id": sprint_row.jira_id,
        "name": sprint_row.name,
        "state": sprint_row.state,
        "issues": [schemas.IssueOut.model_validate(dict(i)) for i in issues],
    })
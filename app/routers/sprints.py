# app/routers/sprints.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, timezone
from .. import schemas, models
from ..database import get_session
from ..services.jira import JiraClient

router = APIRouter()

@router.get("/{sprint_id}/issues", response_model=schemas.SprintWithIssues)
async def get_issues_for_sprint(
    sprint_id: int,
    refresh: bool = False,
    session: AsyncSession = Depends(get_session),
):
    # Fetch sprint row
    stmt = select(models.Sprint).where(models.Sprint.jira_id == sprint_id)
    result = await session.execute(stmt)
    sprint_row = result.scalar_one_or_none()

    # Serve cache only if issues have been synced at least once
    if sprint_row and sprint_row.issues_synced and not refresh:
        issues_res = await session.execute(
            select(models.Issue).where(models.Issue.sprint_id == sprint_row.id)
        )
        issues = issues_res.scalars().all()
        return schemas.SprintWithIssues.model_validate(
            {
                "jira_id": sprint_row.jira_id,
                "name": sprint_row.name,
                "state": sprint_row.state,
                "issues": [schemas.IssueOut.model_validate(i) for i in issues],
            }
        )

    if sprint_row is None and not refresh:
        raise HTTPException(status_code=404, detail="Sprint not cached; try refresh=true")

    # Fetch issues from Jira
    client = JiraClient()
    issues_raw = await client.list_issues_for_sprint(sprint_id)

    if sprint_row is None:
        sprint_row = models.Sprint(jira_id=sprint_id, name=f"Sprint {sprint_id}", board_id=0, state="unknown")
        session.add(sprint_row)
        await session.commit()

    # Replace issues
    await session.execute(delete(models.Issue).where(models.Issue.sprint_id == sprint_row.id))
    for raw in issues_raw:
        f = raw["fields"]
        issue = models.Issue(
            jira_key=raw["key"],
            summary=f.get("summary", ""),
            description=f.get("description"),
            is_subtask=f.get("issuetype", {}).get("subtask", False),
            parent_key=(f.get("parent") or {}).get("key"),
            sprint_id=sprint_row.id,
        )
        session.add(issue)

    # Mark as synced
    sprint_row.issues_synced = datetime.now(timezone.utc)
    await session.commit()

    # Return freshly stored data
    issues_res = await session.execute(select(models.Issue).where(models.Issue.sprint_id == sprint_row.id))
    issues = issues_res.scalars().all()

    return schemas.SprintWithIssues.model_validate(
        {
            "jira_id": sprint_row.jira_id,
            "name": sprint_row.name,
            "state": sprint_row.state,
            "issues": [schemas.IssueOut.model_validate(i) for i in issues],
        }
    )
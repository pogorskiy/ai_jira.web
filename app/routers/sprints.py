from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession
from .. import schemas, models
from ..database import get_session
from ..services.jira import JiraClient

router = APIRouter()


@router.get("/{sprint_id}/issues", response_model=schemas.SprintWithIssues)
async def get_issues_for_sprint(
    sprint_id: int,
    refresh: bool = True,
    session: AsyncSession = Depends(get_session),
):
    # Try to fetch the sprint from the local cache (PostgreSQL)
    stmt = select(models.Sprint).where(models.Sprint.jira_id == sprint_id)
    result = await session.execute(stmt)
    sprint_row = result.scalar_one_or_none()

    # If we have a cached sprint and refresh is not requested, return it
    if sprint_row and not refresh:
        issues_result = await session.execute(
            select(models.Issue).where(models.Issue.sprint_id == sprint_row.id)
        )
        issues = issues_result.scalars().all()
        response = {
            "jira_id": sprint_row.jira_id,
            "name": sprint_row.name,
            "state": sprint_row.state,
            "issues": [schemas.IssueOut.model_validate(issue) for issue in issues],
        }
        return schemas.SprintWithIssues.model_validate(response)

    # No cache and no refresh flag → inform the client
    if not sprint_row and not refresh:
        raise HTTPException(status_code=404, detail="Sprint not cached; try refresh=true")

    # Cache miss or manual refresh → pull fresh data from Jira
    client = JiraClient()
    issues_raw = await client.list_issues_for_sprint(sprint_id)

    # If the sprint does not exist locally, create a placeholder row
    if sprint_row is None:
        sprint_row = models.Sprint(
            jira_id=sprint_id,
            name=f"Sprint {sprint_id}",
            board_id=0,
            state="unknown",
        )
        session.add(sprint_row)
        await session.commit()

    # Replace existing issues with the fresh list
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

    await session.commit()

    # Build and return the response using the freshly stored data
    issues_result = await session.execute(
        select(models.Issue).where(models.Issue.sprint_id == sprint_row.id)
    )
    issues = issues_result.scalars().all()

    response = {
        "jira_id": sprint_row.jira_id,
        "name": sprint_row.name,
        "state": sprint_row.state,
        "issues": [schemas.IssueOut.model_validate(issue) for issue in issues],
    }
    return schemas.SprintWithIssues.model_validate(response)
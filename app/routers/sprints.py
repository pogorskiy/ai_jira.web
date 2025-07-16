from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.dialects.postgresql import insert as pg_insert
from datetime import datetime, timezone
from .. import schemas, models
from ..database import get_session
from ..services.jira import JiraClient
from ..services.openai import summarize_sprint
from openai import AsyncOpenAI
import os

router = APIRouter()

@router.get("/{sprint_id}/issues", response_model=schemas.SprintWithIssues)
async def get_issues_for_sprint(
    sprint_id: int,
    refresh: bool = False,
    session: AsyncSession = Depends(get_session),
):
    # fetch sprint row
    res = await session.execute(select(models.Sprint).where(models.Sprint.jira_id == sprint_id))
    sprint_row = res.scalar_one_or_none()

    # Serve cache only if issues_synced is set and refresh=False
    if sprint_row and sprint_row.issues_synced and not refresh:
        res = await session.execute(
            select(models.Issue).join(models.SprintIssue).where(models.SprintIssue.sprint_id == sprint_row.id)
        )
        issues = res.scalars().all()
        return schemas.SprintWithIssues.model_validate({
            "jira_id": sprint_row.jira_id,
            "name": sprint_row.name,
            "state": sprint_row.state,
            "issues": [schemas.IssueOut.model_validate(i) for i in issues],
        })

    if not sprint_row and not refresh:
        raise HTTPException(404, "Sprint not cached; try refresh=true")

    # fetch from Jira
    client = JiraClient()
    raw_issues = await client.list_issues_for_sprint(sprint_id)

    # ensure sprint exists
    if sprint_row is None:
        sprint_row = models.Sprint(jira_id=sprint_id, name=f"Sprint {sprint_id}")
        session.add(sprint_row)
        await session.commit()

    # delete old associations (not issues)
    await session.execute(delete(models.SprintIssue).where(models.SprintIssue.sprint_id == sprint_row.id))

    for raw in raw_issues:
        f = raw["fields"]
        # upsert Issue (by jira_key)
        res = await session.execute(select(models.Issue).where(models.Issue.jira_key == raw["key"]))
        issue = res.scalar_one_or_none()
        if issue is None:
            issue = models.Issue(
                jira_key=raw["key"],
                summary=f.get("summary", ""),
                description=f.get("description"),
                is_subtask=f.get("issuetype", {}).get("subtask", False),
                parent_key=(f.get("parent") or {}).get("key"),
            )
            session.add(issue)
            await session.flush([issue])  # ensure PK
        # link sprint⇄issue
        await session.execute(
            pg_insert(models.SprintIssue)
            .values(sprint_id=sprint_row.id, issue_id=issue.id)
            .on_conflict_do_nothing()
        )

    sprint_row.issues_synced = datetime.now(timezone.utc)
    await session.commit()

    res = await session.execute(
        select(models.Issue).join(models.SprintIssue).where(models.SprintIssue.sprint_id == sprint_row.id)
    )
    issues = res.scalars().all()

    return schemas.SprintWithIssues.model_validate({
        "jira_id": sprint_row.jira_id,
        "name": sprint_row.name,
        "state": sprint_row.state,
        "issues": [schemas.IssueOut.model_validate(i) for i in issues],
    })


# --- Sprint summary endpoint ---
@router.get("/{sprint_id}/summary")
async def get_sprint_summary(
    sprint_id: int,
    force_refresh: bool = False,
    session: AsyncSession = Depends(get_session),
):
    """
    Return a ChatGPT‑generated summary for the given sprint.

    * `force_refresh=true` pulls fresh data from Jira before summarizing.
    * Response format:
      ```json
      {"sprint_id": 123, "summary": "…"}
      ```
    """
    # Получить спринт из базы
    res = await session.execute(select(models.Sprint).where(models.Sprint.jira_id == sprint_id))
    sprint_row = res.scalar_one_or_none()

    # Если summary уже есть и не требуется обновление — вернуть из базы
    if sprint_row and sprint_row.summary_text and not force_refresh:
        return {"sprint_id": sprint_id, "summary": sprint_row.summary_text}

    # Pull sprint issues (reuse existing logic)
    sprint_data = await get_issues_for_sprint(
        sprint_id=sprint_id,
        refresh=force_refresh,
        session=session,
    )

    summary_text = await summarize_sprint(
        name=sprint_data.name,
        state=sprint_data.state,
        issues=sprint_data.issues,
    )

    # Сохранить summary в базу
    if sprint_row:
        sprint_row.summary_text = summary_text
        sprint_row.summary_updated = datetime.now(timezone.utc)
        await session.commit()

    return {"sprint_id": sprint_id, "summary": summary_text}
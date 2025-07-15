from pydantic import BaseModel, ConfigDict
from typing import List, Optional


class IssueOut(BaseModel):
    jira_key: str
    summary: str
    description: Optional[str]
    is_subtask: bool
    parent_key: Optional[str]

    # Tell Pydantic that we load models from ORM objects / SQLAlchemy rows
    model_config = ConfigDict(from_attributes=True)


class SprintOut(BaseModel):
    jira_id: int
    name: str
    state: str

    model_config = ConfigDict(from_attributes=True)


class SprintWithIssues(SprintOut):
    issues: List[IssueOut]

    model_config = ConfigDict(from_attributes=True)
from datetime import datetime
from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, DateTime, UniqueConstraint
from sqlalchemy.orm import relationship
from .database import Base

class Sprint(Base):
    __tablename__ = "sprints"

    id = Column(Integer, primary_key=True, index=True)
    jira_id = Column(Integer, unique=True, index=True)
    name = Column(String, index=True)
    state = Column(String)
    board_id = Column(Integer, index=True)
    issues_synced = Column(DateTime(timezone=True), nullable=True)
    summary_text = Column(String, nullable=True)
    summary_updated = Column(DateTime(timezone=True), nullable=True)

    # many‑to‑many via association table
    issues = relationship(
        "Issue",
        secondary="sprint_issues",
        back_populates="sprints",
        viewonly=True,
    )

class Issue(Base):
    __tablename__ = "issues"

    id = Column(Integer, primary_key=True, index=True)
    jira_key = Column(String, unique=True, index=True, nullable=False)
    summary = Column(String)
    description = Column(String)
    is_subtask = Column(Boolean, default=False)
    parent_key = Column(String, index=True, nullable=True)

    sprints = relationship(
        "Sprint",
        secondary="sprint_issues",
        back_populates="issues",
        viewonly=True,
    )

class SprintIssue(Base):
    """Association table – one issue may appear in many sprints."""

    __tablename__ = "sprint_issues"
    sprint_id = Column(Integer, ForeignKey("sprints.id", ondelete="CASCADE"), primary_key=True)
    issue_id = Column(Integer, ForeignKey("issues.id",  ondelete="CASCADE"), primary_key=True)
    added_at = Column(DateTime(timezone=True), default=datetime.utcnow)

    __table_args__ = (
        UniqueConstraint("sprint_id", "issue_id", name="uq_sprint_issue"),
    )
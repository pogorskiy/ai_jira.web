# app/models.py
from datetime import datetime
from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from .database import Base

class Sprint(Base):
    __tablename__ = "sprints"

    id = Column(Integer, primary_key=True, index=True)
    jira_id = Column(Integer, unique=True, index=True)
    name = Column(String, index=True)
    state = Column(String)
    board_id = Column(Integer, index=True)

    # Timestamp when issues were last fetched from Jira (NULL = never fetched yet)
    issues_synced = Column(DateTime(timezone=True), nullable=True, index=True)

    issues = relationship("Issue", back_populates="sprint", cascade="all, delete-orphan")

class Issue(Base):
    __tablename__ = "issues"

    id = Column(Integer, primary_key=True, index=True)
    jira_key = Column(String, unique=True, index=True)
    summary = Column(String)
    description = Column(String)
    is_subtask = Column(Boolean, default=False)
    parent_key = Column(String, index=True, nullable=True)
    sprint_id = Column(Integer, ForeignKey("sprints.id", ondelete="CASCADE"))

    sprint = relationship("Sprint", back_populates="issues")
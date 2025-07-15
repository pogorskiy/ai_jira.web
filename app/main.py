# app/main.py

from fastapi import FastAPI
from .routers import boards, sprints

app = FastAPI(title="Jira Sprint Summary API")

# Boards endpoints: /boards/{board_id}/sprints …
app.include_router(boards.router, prefix="/boards", tags=["boards"])

# Sprints endpoints: /sprints/{sprint_id}/issues …
app.include_router(sprints.router, prefix="/sprints", tags=["sprints"])
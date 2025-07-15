# app/main.py

from fastapi import FastAPI, APIRouter
from .routers import boards, sprints

app = FastAPI(title="Jira Sprint Summary API")


api_router = APIRouter(prefix="/api")

api_router.include_router(boards.router, prefix="/boards", tags=["boards"])
api_router.include_router(sprints.router, prefix="/sprints", tags=["sprints"])

app.include_router(api_router)
# Jira Sprint Summary Service

## Prerequisites
* Docker + Docker Compose (recommended) **or** Python 3.11 with virtualenv

## Local quick‑start (Docker Compose)
```bash
cp .env.example .env  # edit credentials
docker compose up --build
```
Browse http://localhost:8000/docs for interactive Swagger UI.

## Local dev (VS Code, no Docker)
```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
export $(cat .env.example | xargs)  # adapt values or use direnv
alembic upgrade head  # TODO: add migrations later
uvicorn app.main:app --reload
```

## Front‑end (React + Vite)
```
npm create vite@latest jira-sprint-ui -- --template react-ts
cd jira-sprint-ui
npm install @mui/material @tanstack/react-query axios
```
A minimal component will fetch `/boards/{id}/sprints` into a dropdown, then `/sprints/{id}/issues` into a material‑ui DataGrid. Use React Query for caching and a **Refresh** button to invalidate the query.

## Deploying to AWS
1. Push Docker image to Amazon ECR.
2. Spin up **AWS ECS Fargate** service (or Elastic Beanstalk) with secrets in AWS Secrets Manager.
3. Use **AWS RDS PostgreSQL** for persistence.
4. (Optional) Add an **AWS CloudFront** + **S3 static site** for the React UI.
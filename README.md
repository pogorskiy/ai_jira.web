# Jira Sprint Summarizer – Local Setup

Lightweight **FastAPI + PostgreSQL** backend and **React + Vite** frontend.  
Fetches sprints / issues from Atlassian Jira, caches them locally, and shows a
table with tool-tips for descriptions.

---

## Prerequisites

| Tool | Minimum version | Check |
|------|-----------------|-------|
| **Python** | 3.11 | `python --version` |
| **Node LTS** | 18 or 20 | `node --version` |
| **npm / pnpm / yarn** | latest | `npm --version` |
| **PostgreSQL** | 14+ | `psql --version` |
| (optional) **Docker & Docker Compose** | — | `docker compose version` |

---

## 1 · Clone the repository

```bash
git clone https://github.com/pogorskiy/ai_jira.web.git
cd ai_jira.web
```

## 2 · Create .env

```bash
cp .env.example .env
```
Edit the file:

```
DATABASE_URL=postgresql+asyncpg://jira:jira@localhost:5432/jira_cache
JIRA_BASE_URL=https://your-domain.atlassian.net
JIRA_EMAIL=you@example.com
JIRA_API_TOKEN=your-api-token
```

## 3 · Start PostgreSQL

```bash
# macOS (Homebrew) example
brew services start postgresql@16
createuser -s jira           # if not yet created
createdb -O jira jira_cache
```

## 4 · Backend

### 4.1 Run without Docker

```bash
python -m venv .venv
source .venv/bin/activate        # Windows: .\.venv\Scripts\Activate
pip install -r requirements.txt
alembic upgrade head             # create tables
uvicorn app.main:app --reload --env-file .env
```

API is now at http://localhost:8000/api
Swagger UI: http://localhost:8000/api/docs


## 5 · Frontend

```bash
cd frontend
npm install
npm run dev                       # http://localhost:5173
```

## 6 · Project layout
```
repo-root/
├─ app/                # FastAPI backend
│  ├─ routers/         # boards.py, sprints.py
│  ├─ services/        # Jira REST client
│  └─ models.py        # ORM + M:N sprint_issues
├─ migrations/         # Alembic revisions
├─ frontend/           # React + TypeScript UI
├─ docker-compose.yml  # db + api
└─ README.md
```

## 7 · VS Code debug
.vscode/launch.json
```jsonc
{
  "version": "0.2.0",
  "configurations": [
    {
      "name": "Debug FastAPI",
      "type": "python",
      "request": "launch",
      "module": "uvicorn",
      "args": ["app.main:app", "--reload", "--env-file", ".env"],
      "cwd": "${workspaceFolder}",
      "console": "integratedTerminal"
    }
  ]
}
```

Press F5 to run backend with the debugger; run npm run dev in
another terminal for the UI.

## 8 · Updating the DB schema
```bash
# change SQLAlchemy models …
alembic revision --autogenerate -m "your message"
alembic upgrade head
```

## 10 · Quick test

	1.	Open http://localhost:5173.
	2.	Click Refresh sprints, pick a sprint, Fetch issues.
	3.	Hover any row – a tooltip shows the issue description.
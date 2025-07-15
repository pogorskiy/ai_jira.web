import os
import httpx
from typing import List, Dict

class JiraClient:
    def __init__(self):
        self.base_url = os.getenv("JIRA_BASE_URL")  # e.g. https://your-domain.atlassian.net
        self.email = os.getenv("JIRA_EMAIL")
        self.token = os.getenv("JIRA_API_TOKEN")
        self.auth = (self.email, self.token)
        self.headers = {"Accept": "application/json"}

    async def list_sprints(self, board_id: int) -> List[Dict]:
        url = f"{self.base_url}/rest/agile/1.0/board/{board_id}/sprint"
        async with httpx.AsyncClient() as client:
            resp = await client.get(url, auth=self.auth, headers=self.headers)
            resp.raise_for_status()
            return resp.json().get("values", [])

    async def list_issues_for_sprint(self, sprint_id: int) -> List[Dict]:
        url = f"{self.base_url}/rest/agile/1.0/sprint/{sprint_id}/issue?maxResults=1000"
        async with httpx.AsyncClient() as client:
            resp = await client.get(url, auth=self.auth, headers=self.headers)
            resp.raise_for_status()
            return resp.json().get("issues", [])
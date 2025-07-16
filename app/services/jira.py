import os
import httpx
from typing import List, Dict

class JiraClient:
    def __init__(self):
        # Read Jira credentials from environment variables
        self.base_url = os.getenv("JIRA_BASE_URL")  # e.g. https://your-domain.atlassian.net
        self.email = os.getenv("JIRA_EMAIL")
        self.token = os.getenv("JIRA_API_TOKEN")
        # Check that all required environment variables are set
        if not all([self.base_url, self.email, self.token]):
            raise RuntimeError("JIRA_BASE_URL, JIRA_EMAIL, JIRA_API_TOKEN must be set in environment")
        self.auth = (self.email, self.token)
        self.headers = {"Accept": "application/json"}

    async def list_sprints(self, board_id: int) -> List[Dict]:
        """
        Get list of sprints for a board.
        """
        url = f"{self.base_url}/rest/agile/1.0/board/{board_id}/sprint"
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.get(url, auth=self.auth, headers=self.headers)
                resp.raise_for_status()
                return resp.json().get("values", [])
        except httpx.HTTPError as e:
            # Log and raise error if Jira API call fails
            raise RuntimeError(f"Jira API error (list_sprints): {e}")

    async def list_issues_for_sprint(self, sprint_id: int, max_results: int = 1000) -> List[Dict]:
        """
        Get issues for a sprint.
        """
        url = f"{self.base_url}/rest/agile/1.0/sprint/{sprint_id}/issue?maxResults={max_results}"
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.get(url, auth=self.auth, headers=self.headers)
                resp.raise_for_status()
                return resp.json().get("issues", [])
        except httpx.HTTPError as e:
            raise RuntimeError(f"Jira API error (list_issues_for_sprint): {e}")
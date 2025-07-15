"""High-level helpers for calling ChatGPT o3."""

from typing import List
from openai import AsyncOpenAI
import os

_client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))


async def summarize_sprint(*, name: str, state: str, issues: List):
    """
    Generate a Russian sprint summary (main vs. secondary goals).

    Args:
        name:  Sprint name.
        state: Sprint state (e.g., active, closed).
        issues: Iterable with attrs jira_key, summary, parent_key.
    Returns:
        str – summary text in Russian.
    """
    def issue_line(it) -> str:
        parent = f"(parent: {getattr(it, 'parent_key', None)})" if getattr(it, "parent_key", None) else ""
        return f"- {it.jira_key}: {it.summary} {parent}".strip()

    bullet_list = "\n".join(issue_line(i) for i in issues)

    system_msg = (
        "You are an Agile assistant. "
        "Descriptions of issues may be in Russian or English. "
        "Given a sprint backlog, produce two lists in Russian: "
        "1) main goals, 2) secondary goals."
    )
    user_msg = (
        f"Sprint name: {name}\n"
        f"Sprint state: {state}\n"
        "Issues:\n"
        f"{bullet_list}"
    )

    resp = await _client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": system_msg},
            {"role": "user", "content": user_msg},
        ],
        max_tokens=1000,
        temperature=1,
    )
    return resp.choices[0].message.content.strip()
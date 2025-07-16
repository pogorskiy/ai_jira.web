"""High-level helpers for calling ChatGPT o3."""

from typing import List
from openai import AsyncOpenAI
import os

# Check that OpenAI API key is set
api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    raise RuntimeError("OPENAI_API_KEY must be set in environment")

_client = AsyncOpenAI(api_key=api_key)


async def summarize_sprint(
    *,
    name: str,
    state: str,
    issues: List,
    model: str = "gpt-4o",
    temperature: float = 0.3
):
    """
    Generate a Russian sprint summary (main vs. secondary goals).

    Args:
        name:  Sprint name.
        state: Sprint state (e.g., active, closed).
        issues: Iterable with attrs jira_key, summary, parent_key.
        model: OpenAI model name.
        temperature: Sampling temperature.
    Returns:
        str – summary text in Russian.
    Raises:
        RuntimeError if OpenAI API call fails.
    """
    def issue_line(it) -> str:
        # Format issue line for prompt
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

    try:
        resp = await _client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system_msg},
                {"role": "user", "content": user_msg},
            ],
            max_tokens=1000,
            temperature=temperature,
        )
        return resp.choices[0].message.content.strip()
    except Exception as e:
        # Raise error if OpenAI API call fails
        raise RuntimeError(f"OpenAI API error: {e}")
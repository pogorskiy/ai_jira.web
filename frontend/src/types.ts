export interface Sprint {
  jira_id: number
  name: string
  state: string
}

export interface Issue {
  jira_key: string;
  summary: string;
  description: string | null;
  is_subtask: boolean;
  parent_key: string | null;
}

export interface SprintWithIssues {
  jira_id: number;
  name: string;
  state: string;
  issues: Issue[];
}
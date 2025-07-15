import { useState } from 'react';
import axios from 'axios';
import type { Sprint } from './types';
import {
  MantineProvider,
  Container,
  Button,
  Select,
  Table,
  ScrollArea,
  Group,
} from '@mantine/core';
import {
  QueryClient,
  QueryClientProvider,
  useQuery,
  useQueryClient,
} from '@tanstack/react-query';

// initialise react-query
const queryClient = new QueryClient();

// Axios instance that goes via Vite proxy (/api → :8000)
const api = axios.create({ baseURL: '/api' });

/* --------------------------- helper functions --------------------------- */

async function fetchSprints(boardId: number, force: boolean) {
  const { data } = await api.get(
    `/boards/${boardId}/sprints${force ? '?refresh=true' : ''}`,
  );
  // Descending order by jira_id
  return (data as Sprint[]).sort((a, b) => b.jira_id - a.jira_id);
}

async function fetchIssues(sprintId: number, force: boolean) {
  const { data } = await api.get(
    `/sprints/${sprintId}/issues${force ? '?refresh=true' : ''}`,
  );
  return data; // { jira_id, name, state, issues: [...] }
}

/* --------------------------- page component ---------------------------- */

function SprintPage() {
  const BOARD_ID = 36; // <-- put your board id here or lift to state
  const [selected, setSelected] = useState<string | null>(null);
  const queryClient = useQueryClient();

  /* ------ sprints list ------ */
const { data: sprints = [], isFetching: sprintsFetching } = useQuery<Sprint[]>({
  queryKey: ['sprints', BOARD_ID],
  queryFn: () => fetchSprints(BOARD_ID, false),
  staleTime: 5 * 60 * 1000,
});

  /* ------ issues for chosen sprint ------ */
  const {
    data: issuesData,
    isFetching: issuesFetching,
    refetch: refetchIssues,
  } = useQuery({
    queryKey: ['issues', selected],
    queryFn: () => fetchIssues(Number(selected), false),
    enabled: false, // run manually via button
  });

  /* ------------------- handlers ------------------- */

  const handleRefreshSprints = async () => {
    await queryClient.fetchQuery({
      queryKey: ['sprints', BOARD_ID],
      queryFn: () => fetchSprints(BOARD_ID, true),
    });
  };

  const handleRefreshIssues = async () => {
    if (!selected) return;
    await queryClient.fetchQuery({
      queryKey: ['issues', selected],
      queryFn: () => fetchIssues(Number(selected), true),
    });
  };

  return (
    <Container py="md">
      <Group mb="md">
        <Select
          placeholder="Select sprint"
          data={sprints.map((s) => ({
            value: String(s.jira_id),
            label: `${s.name} (${s.state})`,
          }))}
          value={selected}
          onChange={setSelected}
          searchable
          disabled={sprintsFetching}
          w={300}
        />

        <Button loading={sprintsFetching} onClick={handleRefreshSprints}>
          Refresh sprints
        </Button>

        <Button
          disabled={!selected}
          loading={issuesFetching}
          onClick={() => refetchIssues()}
        >
          Fetch issues
        </Button>

        <Button
          disabled={!selected}
          variant="light"
          loading={issuesFetching}
          onClick={handleRefreshIssues}
        >
          Refresh issues
        </Button>
      </Group>

      {issuesData && (
        <ScrollArea h={500}>
          <Table striped highlightOnHover withBorder maw={900} mx="auto">
            <thead>
              <tr>
                <th>Key</th>
                <th>Summary</th>
                <th>Sub-task</th>
                <th>Parent</th>
              </tr>
            </thead>
            <tbody>
              {issuesData.issues.map((it: any) => (
                <tr key={it.jira_key}>
                  <td>{it.jira_key}</td>
                  <td>{it.summary}</td>
                  <td>{it.is_subtask ? '✔' : ''}</td>
                  <td>{it.parent_key || '—'}</td>
                </tr>
              ))}
            </tbody>
          </Table>
        </ScrollArea>
      )}
    </Container>
  );
}

/* --------------------------- app root --------------------------- */

export default function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <MantineProvider withNormalizeCSS withGlobalStyles>
        <SprintPage />
      </MantineProvider>
    </QueryClientProvider>
  );
}
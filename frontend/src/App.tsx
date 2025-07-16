import { useState } from 'react';
import axios from 'axios';
import type { Sprint, Issue, SprintWithIssues } from './types';
import {
  MantineProvider,
  Container,
  Button,
  Select,
  Table,
  ScrollArea,
  Group,
  Tooltip,
  SimpleGrid,
  Paper,
  Textarea,
  Loader,
} from '@mantine/core';
import {
  QueryClient,
  QueryClientProvider,
  useQuery,
  useQueryClient,
  useMutation,
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

async function fetchSummary(sprintId: number) {
  const { data } = await api.get(`/sprints/${sprintId}/summary`);
  return data as { sprint_id: number; summary: string };
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
} = useQuery<SprintWithIssues>({
  queryKey: ['issues', selected],
  queryFn: () => fetchIssues(Number(selected), false),
  enabled: false,
});

/* ------ summary mutation ------ */
const summaryMutation = useMutation({
  mutationFn: () => fetchSummary(Number(selected)),
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
    <Container py="md" fluid style={{ height: '100vh', width: '100vw', maxWidth: '100vw' }}>
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

        <Button
          disabled={!selected}
          loading={summaryMutation.isPending}
          onClick={() => summaryMutation.mutate()}
        >
          Сделать&nbsp;саммари
        </Button>
      </Group>

      <SimpleGrid cols={{ base: 1, md: 2 }} spacing="lg" style={{ height: 'calc(100vh - 100px)' }}>
        {/* Issues table */}
        <ScrollArea h="100%" style={{ height: '100%', minHeight: 0 }}>
          {issuesData ? (
            <Table striped highlightOnHover withBorder maw={1800} mx="auto">
              <thead>
                <tr>
                  <th>Key</th>
                  <th>Summary</th>
                  <th>Sub-task</th>
                  <th>Parent</th>
                </tr>
              </thead>
              <tbody>
                {issuesData.issues.map((it: Issue) => (
                  <Tooltip
                    key={it.jira_key}
                    label={it.description || 'No description'}
                    multiline
                    w={400}
                    withArrow
                    transitionProps={{ duration: 150 }}
                  >
                    <tr>
                      <td>{it.jira_key}</td>
                      <td>{it.summary}</td>
                      <td>{it.is_subtask ? '✔' : ''}</td>
                      <td>{it.parent_key || '—'}</td>
                    </tr>
                  </Tooltip>
                ))}
              </tbody>
            </Table>
          ) : (
            <em>Select a sprint and click "Fetch issues"</em>
          )}
        </ScrollArea>

        {/* Summary panel */}
        <Paper shadow="sm" p="md" withBorder style={{ height: '100%' }}>
          {summaryMutation.isPending && <Loader />}
          {summaryMutation.data && (
            <Textarea
              minRows={15}
              value={summaryMutation.data.summary}
              readOnly
              autosize
              label="Саммари спринта"
            />
          )}
          {!summaryMutation.isPending && !summaryMutation.data && (
            <em>Click “Сделать саммари” to generate the sprint summary.</em>
          )}
        </Paper>
      </SimpleGrid>
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
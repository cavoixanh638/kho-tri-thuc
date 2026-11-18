import { Alert, Button, Container, Stack, Text, Title } from '@mantine/core';
import { useEffect, useState } from 'react';

type ApiStatus = 'checking' | 'ready' | 'unavailable';

const statusMessages: Record<ApiStatus, string> = {
  checking: 'Đang kiểm tra kết nối…',
  ready: 'API đã kết nối với PostgreSQL.',
  unavailable: 'Chưa kết nối được với API hoặc PostgreSQL.',
};

export function App() {
  const [status, setStatus] = useState<ApiStatus>('checking');
  const [attempt, setAttempt] = useState(0);

  useEffect(() => {
    const controller = new AbortController();
    const timeout = window.setTimeout(() => controller.abort(), 5000);
    let active = true;

    async function checkApi() {
      try {
        const response = await fetch('/api/v1/health', {
          cache: 'no-store',
          signal: controller.signal,
        });
        const payload: { status?: string } = response.ok ? await response.json() : {};

        if (active) {
          setStatus(payload.status === 'ready' ? 'ready' : 'unavailable');
        }
      } catch {
        if (active) {
          setStatus('unavailable');
        }
      } finally {
        window.clearTimeout(timeout);
      }
    }

    void checkApi();

    return () => {
      active = false;
      window.clearTimeout(timeout);
      controller.abort();
    };
  }, [attempt]);

  function retry() {
    setStatus('checking');
    setAttempt((previous) => previous + 1);
  }

  return (
    <Container component="main" size="xs" py="xl">
      <Stack align="start" gap="md">
        <Title order={1}>Kho Tri Thức</Title>
        <Text c="dimmed">Kiểm tra kết nối của môi trường phát triển.</Text>
        <Alert w="100%" color={status === 'unavailable' ? 'red' : 'blue'} role="status">
          {statusMessages[status]}
        </Alert>
        <Button onClick={retry} loading={status === 'checking'} variant="default">
          Kiểm tra lại
        </Button>
      </Stack>
    </Container>
  );
}

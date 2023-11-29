import { Button, Group, Stack, Text } from '@mantine/core';
import { useState } from 'react';
import AppLayout from '@/components/layouts/AppLayout';
import LocalModePanel from '@/components/organisms/LocalModePanel';
import RemoteModePanel from '@/components/organisms/RemoteModePanel';

export default function AppView() {
  const [mode, setMode] = useState<'local' | 'remote' | null>(null);
  return (
    <AppLayout>
      <Stack
        align="center"
        justify="center"
        w="100dvw"
        h="100dvh"
        maw="100dvw"
        mah="100dvh"
        className="overflow-hidden"
      >
        {mode === null ? (
          <>
            <Text>Choose how to send data for inference</Text>
            <Group>
              <Button onClick={() => setMode('local')}>Use local file</Button>
              <Button onClick={() => setMode('remote')}>Use webcam</Button>
            </Group>
          </>
        ) : mode === 'remote' ? (
          <RemoteModePanel />
        ) : (
          <LocalModePanel />
        )}
      </Stack>
    </AppLayout>
  );
}

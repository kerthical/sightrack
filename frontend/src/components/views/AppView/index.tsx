import { SegmentedControl, Stack } from '@mantine/core';
import { useState } from 'react';
import AppLayout from '@/components/layouts/AppLayout';
import LocalModePanel from '@/components/organisms/LocalModePanel';
import RemoteModePanel from '@/components/organisms/RemoteModePanel';

export default function AppView() {
  const [mode, setMode] = useState('remote');
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
        <SegmentedControl
          value={mode}
          onChange={setMode}
          data={[
            {
              label: 'Use web camera',
              value: 'remote',
            },
            {
              label: 'Use local file',
              value: 'local',
            },
          ]}
        />
        {mode === 'remote' ? <RemoteModePanel /> : <LocalModePanel />}
      </Stack>
    </AppLayout>
  );
}

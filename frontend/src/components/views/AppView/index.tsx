import { Box, SegmentedControl, Stack } from '@mantine/core';
import { useState } from 'react';
import AppLayout from '@/components/layouts/AppLayout';
import LocalModePanel from '@/components/organisms/LocalModePanel';
import RemoteModePanel from '@/components/organisms/RemoteModePanel';

export default function AppView() {
  const [mode, setMode] = useState('remote');
  return (
    <AppLayout>
      <Box
        w="100dvw"
        h="100dvh"
        maw="100dvw"
        mah="100dvh"
        className="flex flex-col items-center justify-center overflow-hidden"
      >
        <Stack>
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
      </Box>
    </AppLayout>
  );
}

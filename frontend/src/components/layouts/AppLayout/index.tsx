import { MantineProvider } from '@mantine/core';
import { ReactNode, StrictMode } from 'react';
import '@/assets/styles/tailwind.css';
import { theme } from '@/assets/styles/theme.ts';
import '@mantine/core/styles.css';

interface AppLayoutProps {
  children?: ReactNode;
}

export default function AppLayout({ children }: AppLayoutProps) {
  return (
    <StrictMode>
      <MantineProvider defaultColorScheme="dark" theme={theme}>
        {children}
      </MantineProvider>
    </StrictMode>
  );
}

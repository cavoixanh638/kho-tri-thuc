import '@mantine/core/styles.css';
import './styles.css';

import { createTheme, MantineProvider } from '@mantine/core';
import { StrictMode } from 'react';
import { createRoot } from 'react-dom/client';
import { App } from './App';

const theme = createTheme({
  fontFamily: 'Geist, system-ui, sans-serif',
  primaryColor: 'dark',
  primaryShade: 9,
  defaultRadius: 6,
});

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <MantineProvider theme={theme} forceColorScheme="light">
      <App />
    </MantineProvider>
  </StrictMode>,
);

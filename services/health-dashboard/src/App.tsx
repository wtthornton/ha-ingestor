import React from 'react';
import { RouterProvider } from 'react-router-dom';
import { LayoutProvider } from './contexts/LayoutContext';
import { NotificationProvider } from './contexts/NotificationContext';
import { ThemeProvider } from './contexts/ThemeContext';
import router from './router';

function App() {
  return (
    <ThemeProvider>
      <LayoutProvider>
        <NotificationProvider>
          <RouterProvider router={router} />
        </NotificationProvider>
      </LayoutProvider>
    </ThemeProvider>
  );
}

export default App;

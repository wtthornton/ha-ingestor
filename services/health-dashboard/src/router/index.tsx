import { createBrowserRouter, RouterProvider } from 'react-router-dom';
import { Dashboard } from '../components/Dashboard';
import { Monitoring } from '../components/Monitoring';
import { Settings } from '../components/Settings';
import { ErrorBoundary } from '../components/ErrorBoundary';

const router = createBrowserRouter([
  { 
    path: "/", 
    Component: Dashboard,
    errorElement: <ErrorBoundary />
  },
  { 
    path: "/monitoring", 
    Component: Monitoring,
    errorElement: <ErrorBoundary />
  },
  { 
    path: "/settings", 
    Component: Settings,
    errorElement: <ErrorBoundary />
  }
]);

export default router;

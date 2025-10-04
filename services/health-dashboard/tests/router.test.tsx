import React from 'react';
import { render, screen } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { LayoutProvider } from '../src/contexts/LayoutContext';
import Dashboard from '../src/components/Dashboard';
import Monitoring from '../src/components/Monitoring';
import Settings from '../src/components/Settings';

// Helper function to render component with router and layout provider
const renderWithRouter = (component: React.ReactElement, initialRoute = '/') => {
  return render(
    <LayoutProvider>
      <MemoryRouter initialEntries={[initialRoute]}>
        {component}
      </MemoryRouter>
    </LayoutProvider>
  );
};

describe('Router', () => {
  test('renders dashboard component on root route', () => {
    renderWithRouter(<Dashboard />, '/');
    
    // Check that Dashboard component is rendered
    expect(screen.getByText('Dashboard Overview')).toBeInTheDocument();
  });

  test('renders monitoring component on /monitoring route', () => {
    renderWithRouter(<Monitoring />, '/monitoring');
    
    // Check that Monitoring component is rendered
    expect(screen.getByText('System Monitoring')).toBeInTheDocument();
  });

  test('renders settings component on /settings route', () => {
    renderWithRouter(<Settings />, '/settings');
    
    // Check that Settings component is rendered
    expect(screen.getByRole('heading', { level: 1 })).toHaveTextContent('Settings');
  });

  test('renders navigation on all routes', () => {
    // Test dashboard route
    const { unmount } = renderWithRouter(<Dashboard />, '/');
    expect(screen.getByText('Health Dashboard')).toBeInTheDocument();
    expect(screen.getByText('Dashboard')).toBeInTheDocument();
    expect(screen.getByText('Monitoring')).toBeInTheDocument();
    expect(screen.getByText('Settings')).toBeInTheDocument();
    unmount();

    // Test monitoring route
    renderWithRouter(<Monitoring />, '/monitoring');
    expect(screen.getByText('Health Dashboard')).toBeInTheDocument();
    expect(screen.getByText('Dashboard')).toBeInTheDocument();
    expect(screen.getByText('Monitoring')).toBeInTheDocument();
    expect(screen.getByText('Settings')).toBeInTheDocument();
  });

  test('navigation links work correctly', () => {
    renderWithRouter(<Dashboard />, '/');
    
    // Check that all navigation links are present
    const dashboardLink = screen.getByText('Dashboard').closest('a');
    const monitoringLink = screen.getByText('Monitoring').closest('a');
    const settingsLink = screen.getByText('Settings').closest('a');
    
    expect(dashboardLink).toHaveAttribute('href', '/');
    expect(monitoringLink).toHaveAttribute('href', '/monitoring');
    expect(settingsLink).toHaveAttribute('href', '/settings');
  });
});

import React from 'react';
import { render, screen } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import { Navigation } from '../../src/components/Navigation';

// Helper function to render with router
const renderWithRouter = (component: React.ReactElement) => {
  return render(
    <BrowserRouter>
      {component}
    </BrowserRouter>
  );
};

describe('Navigation', () => {
  test('renders navigation component', () => {
    renderWithRouter(<Navigation />);
    
    expect(screen.getByText('Health Dashboard')).toBeInTheDocument();
    expect(screen.getByText('Home Assistant Ingestor')).toBeInTheDocument();
  });

  test('renders all navigation links', () => {
    renderWithRouter(<Navigation />);
    
    expect(screen.getByText('Dashboard')).toBeInTheDocument();
    expect(screen.getByText('Monitoring')).toBeInTheDocument();
    expect(screen.getByText('Settings')).toBeInTheDocument();
  });

  test('navigation links have correct href attributes', () => {
    renderWithRouter(<Navigation />);
    
    const dashboardLink = screen.getByText('Dashboard').closest('a');
    const monitoringLink = screen.getByText('Monitoring').closest('a');
    const settingsLink = screen.getByText('Settings').closest('a');
    
    expect(dashboardLink).toHaveAttribute('href', '/');
    expect(monitoringLink).toHaveAttribute('href', '/monitoring');
    expect(settingsLink).toHaveAttribute('href', '/settings');
  });

  test('navigation links have correct classes', () => {
    renderWithRouter(<Navigation />);
    
    const dashboardLink = screen.getByText('Dashboard').closest('a');
    const monitoringLink = screen.getByText('Monitoring').closest('a');
    const settingsLink = screen.getByText('Settings').closest('a');
    
    // Check that links have the expected CSS classes
    expect(dashboardLink).toHaveClass('px-3', 'py-2', 'rounded-md', 'text-sm', 'font-medium');
    expect(monitoringLink).toHaveClass('px-3', 'py-2', 'rounded-md', 'text-sm', 'font-medium');
    expect(settingsLink).toHaveClass('px-3', 'py-2', 'rounded-md', 'text-sm', 'font-medium');
  });

  test('navigation has correct structure', () => {
    renderWithRouter(<Navigation />);
    
    const nav = screen.getByRole('navigation');
    expect(nav).toBeInTheDocument();
    expect(nav).toHaveClass('bg-gray-800', 'text-white', 'p-4');
  });

  test('brand link has correct href', () => {
    renderWithRouter(<Navigation />);
    
    const brandLink = screen.getByText('Health Dashboard').closest('a');
    expect(brandLink).toHaveAttribute('href', '/');
  });

  test('brand link has correct styling', () => {
    renderWithRouter(<Navigation />);
    
    const brandLink = screen.getByText('Health Dashboard').closest('a');
    expect(brandLink).toHaveClass('text-xl', 'font-bold', 'text-white', 'hover:text-gray-300');
  });
});

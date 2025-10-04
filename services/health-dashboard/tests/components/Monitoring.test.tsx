import React from 'react';
import { render, screen } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import { Monitoring } from '../../src/components/Monitoring';

// Helper function to render with router
const renderWithRouter = (component: React.ReactElement) => {
  return render(
    <BrowserRouter>
      {component}
    </BrowserRouter>
  );
};

describe('Monitoring', () => {
  test('renders monitoring page', () => {
    renderWithRouter(<Monitoring />);
    
    expect(screen.getByText('System Monitoring')).toBeInTheDocument();
  });

  test('renders navigation component', () => {
    renderWithRouter(<Monitoring />);
    
    // Check that Navigation component is rendered
    expect(screen.getByText('Health Dashboard')).toBeInTheDocument();
    expect(screen.getByText('Dashboard')).toBeInTheDocument();
    expect(screen.getByText('Monitoring')).toBeInTheDocument();
    expect(screen.getByText('Settings')).toBeInTheDocument();
  });

  test('displays placeholder content', () => {
    renderWithRouter(<Monitoring />);
    
    expect(screen.getByText(/Advanced monitoring features will be implemented/)).toBeInTheDocument();
  });

  test('shows coming soon section', () => {
    renderWithRouter(<Monitoring />);
    
    expect(screen.getByText('Coming Soon')).toBeInTheDocument();
    expect(screen.getByText('Real-time system metrics')).toBeInTheDocument();
    expect(screen.getByText('Interactive charts and graphs')).toBeInTheDocument();
    expect(screen.getByText('Performance monitoring')).toBeInTheDocument();
    expect(screen.getByText('Alert management')).toBeInTheDocument();
  });

  test('has correct styling', () => {
    renderWithRouter(<Monitoring />);
    
    const mainElement = screen.getByRole('main');
    expect(mainElement).toHaveClass('max-w-7xl', 'mx-auto', 'px-4', 'sm:px-6', 'lg:px-8', 'py-8');
    
    const cardElement = screen.getByText('System Monitoring').closest('div');
    expect(cardElement).toHaveClass('bg-white', 'rounded-lg', 'shadow-md', 'p-6');
  });

  test('has correct page structure', () => {
    renderWithRouter(<Monitoring />);
    
    // Check for main heading
    expect(screen.getByRole('heading', { level: 1 })).toHaveTextContent('System Monitoring');
    
    // Check for main content area
    expect(screen.getByRole('main')).toBeInTheDocument();
  });
});

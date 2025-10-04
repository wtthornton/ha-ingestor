import React from 'react';
import { render, screen } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import { Settings } from '../../src/components/Settings';

// Helper function to render with router
const renderWithRouter = (component: React.ReactElement) => {
  return render(
    <BrowserRouter>
      {component}
    </BrowserRouter>
  );
};

describe('Settings', () => {
  test('renders settings page', () => {
    renderWithRouter(<Settings />);
    
    expect(screen.getByRole('heading', { level: 1 })).toHaveTextContent('Settings');
  });

  test('renders navigation component', () => {
    renderWithRouter(<Settings />);
    
    // Check that Navigation component is rendered
    expect(screen.getByText('Health Dashboard')).toBeInTheDocument();
    expect(screen.getByText('Dashboard')).toBeInTheDocument();
    expect(screen.getByText('Monitoring')).toBeInTheDocument();
    expect(screen.getAllByText('Settings')).toHaveLength(2); // Navigation link and page heading
  });

  test('displays placeholder content', () => {
    renderWithRouter(<Settings />);
    
    expect(screen.getByText(/Configuration and settings will be implemented/)).toBeInTheDocument();
  });

  test('shows coming soon section', () => {
    renderWithRouter(<Settings />);
    
    expect(screen.getByText('Coming Soon')).toBeInTheDocument();
    expect(screen.getByText('Theme switching (light/dark mode)')).toBeInTheDocument();
    expect(screen.getByText('User preferences')).toBeInTheDocument();
    expect(screen.getByText('System configuration')).toBeInTheDocument();
    expect(screen.getByText('Notification settings')).toBeInTheDocument();
  });

  test('has correct styling', () => {
    renderWithRouter(<Settings />);
    
    const mainElement = screen.getByRole('main');
    expect(mainElement).toHaveClass('max-w-7xl', 'mx-auto', 'px-4', 'sm:px-6', 'lg:px-8', 'py-8');
    
    const cardElement = screen.getByRole('heading', { level: 1 }).closest('div');
    expect(cardElement).toHaveClass('bg-white', 'rounded-lg', 'shadow-md', 'p-6');
  });

  test('has correct page structure', () => {
    renderWithRouter(<Settings />);
    
    // Check for main heading
    expect(screen.getByRole('heading', { level: 1 })).toHaveTextContent('Settings');
    
    // Check for main content area
    expect(screen.getByRole('main')).toBeInTheDocument();
  });

  test('coming soon section has correct styling', () => {
    renderWithRouter(<Settings />);
    
    const comingSoonSection = screen.getByText('Coming Soon').closest('div');
    expect(comingSoonSection).toHaveClass('bg-green-50', 'border', 'border-green-200', 'rounded-md');
  });
});

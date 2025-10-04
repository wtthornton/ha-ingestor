import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { LayoutProvider, useLayout } from '../../src/contexts/LayoutContext';
import { LAYOUT_CONFIGS, DEFAULT_LAYOUT } from '../../src/config/layouts';

// Test component that uses the layout context
const TestComponent = () => {
  const { layoutState, setCurrentLayout, getCurrentLayoutConfig, isTransitioning } = useLayout();
  
  return (
    <div>
      <div data-testid="current-layout">{layoutState.currentLayout}</div>
      <div data-testid="available-layouts">{layoutState.availableLayouts.length}</div>
      <div data-testid="is-transitioning">{isTransitioning.toString()}</div>
      <button 
        data-testid="set-detailed" 
        onClick={() => setCurrentLayout('detailed')}
      >
        Set Detailed
      </button>
      <button 
        data-testid="set-mobile" 
        onClick={() => setCurrentLayout('mobile')}
      >
        Set Mobile
      </button>
      <button 
        data-testid="set-invalid" 
        onClick={() => setCurrentLayout('invalid')}
      >
        Set Invalid
      </button>
      <div data-testid="current-config-name">
        {getCurrentLayoutConfig()?.name || 'null'}
      </div>
    </div>
  );
};

describe('LayoutContext', () => {
  beforeEach(() => {
    // Clear localStorage before each test
    localStorage.clear();
  });

  test('provides default layout state', () => {
    render(
      <LayoutProvider>
        <TestComponent />
      </LayoutProvider>
    );

    expect(screen.getByTestId('current-layout')).toHaveTextContent(DEFAULT_LAYOUT);
    expect(screen.getByTestId('available-layouts')).toHaveTextContent('4');
    expect(screen.getByTestId('is-transitioning')).toHaveTextContent('false');
    expect(screen.getByTestId('current-config-name')).toHaveTextContent('Overview');
  });

  test('allows changing layout', async () => {
    render(
      <LayoutProvider>
        <TestComponent />
      </LayoutProvider>
    );

    // Initially on overview layout
    expect(screen.getByTestId('current-layout')).toHaveTextContent('overview');
    expect(screen.getByTestId('current-config-name')).toHaveTextContent('Overview');

    // Click to change to detailed layout
    fireEvent.click(screen.getByTestId('set-detailed'));

    // Should show transition state briefly
    expect(screen.getByTestId('is-transitioning')).toHaveTextContent('true');

    // Wait for transition to complete
    await waitFor(() => {
      expect(screen.getByTestId('is-transitioning')).toHaveTextContent('false');
    });

    expect(screen.getByTestId('current-layout')).toHaveTextContent('detailed');
    expect(screen.getByTestId('current-config-name')).toHaveTextContent('Detailed');
  });

  test('handles invalid layout gracefully', () => {
    const consoleSpy = vi.spyOn(console, 'warn').mockImplementation(() => {});
    
    render(
      <LayoutProvider>
        <TestComponent />
      </LayoutProvider>
    );

    // Click to set invalid layout
    fireEvent.click(screen.getByTestId('set-invalid'));

    // Should warn about invalid layout
    expect(consoleSpy).toHaveBeenCalledWith('Layout invalid not found');
    
    // Layout should remain unchanged
    expect(screen.getByTestId('current-layout')).toHaveTextContent('overview');
    
    consoleSpy.mockRestore();
  });

  test('persists layout to localStorage', async () => {
    render(
      <LayoutProvider>
        <TestComponent />
      </LayoutProvider>
    );

    // Change layout
    fireEvent.click(screen.getByTestId('set-mobile'));

    await waitFor(() => {
      expect(screen.getByTestId('current-layout')).toHaveTextContent('mobile');
    });

    // Check localStorage
    expect(localStorage.getItem('dashboard-layout')).toBe('mobile');
  });

  test('loads layout from localStorage on mount', () => {
    // Set layout in localStorage before rendering
    localStorage.setItem('dashboard-layout', 'detailed');

    render(
      <LayoutProvider>
        <TestComponent />
      </LayoutProvider>
    );

    expect(screen.getByTestId('current-layout')).toHaveTextContent('detailed');
    expect(screen.getByTestId('current-config-name')).toHaveTextContent('Detailed');
  });

  test('ignores invalid layout in localStorage', () => {
    // Set invalid layout in localStorage
    localStorage.setItem('dashboard-layout', 'invalid-layout');

    render(
      <LayoutProvider>
        <TestComponent />
      </LayoutProvider>
    );

    // Should fall back to default
    expect(screen.getByTestId('current-layout')).toHaveTextContent(DEFAULT_LAYOUT);
  });

  test('throws error when used outside provider', () => {
    const consoleSpy = vi.spyOn(console, 'error').mockImplementation(() => {});
    
    expect(() => {
      render(<TestComponent />);
    }).toThrow('useLayout must be used within a LayoutProvider');
    
    consoleSpy.mockRestore();
  });
});

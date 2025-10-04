import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { LayoutProvider } from '../../src/contexts/LayoutContext';
import { LayoutSwitcher } from '../../src/components/LayoutSwitcher';

const renderWithProvider = (component: React.ReactElement) => {
  return render(
    <LayoutProvider>
      {component}
    </LayoutProvider>
  );
};

describe('LayoutSwitcher', () => {
  beforeEach(() => {
    localStorage.clear();
  });

  test('renders layout switcher with all options', () => {
    renderWithProvider(<LayoutSwitcher />);

    expect(screen.getByLabelText('Layout:')).toBeInTheDocument();
    
    const select = screen.getByRole('combobox');
    expect(select).toBeInTheDocument();
    
    // Check all layout options are present
    expect(screen.getByRole('option', { name: 'Overview' })).toBeInTheDocument();
    expect(screen.getByRole('option', { name: 'Detailed' })).toBeInTheDocument();
    expect(screen.getByRole('option', { name: 'Mobile' })).toBeInTheDocument();
    expect(screen.getByRole('option', { name: 'Compact' })).toBeInTheDocument();
  });

  test('shows current layout as selected', () => {
    renderWithProvider(<LayoutSwitcher />);

    const select = screen.getByRole('combobox');
    expect(select).toHaveValue('overview');
  });

  test('changes layout when selection changes', async () => {
    renderWithProvider(<LayoutSwitcher />);

    const select = screen.getByRole('combobox');
    
    // Change to detailed layout
    fireEvent.change(select, { target: { value: 'detailed' } });

    await waitFor(() => {
      expect(select).toHaveValue('detailed');
    });

    // Check localStorage was updated
    expect(localStorage.getItem('dashboard-layout')).toBe('detailed');
  });

  test('shows transition indicator when switching', async () => {
    renderWithProvider(<LayoutSwitcher />);

    const select = screen.getByRole('combobox');
    
    // Change layout
    fireEvent.change(select, { target: { value: 'mobile' } });

    // Should show transition indicator
    expect(screen.getByText('Switching...')).toBeInTheDocument();
    expect(screen.getByRole('combobox')).toBeDisabled();

    // Wait for transition to complete
    await waitFor(() => {
      expect(screen.queryByText('Switching...')).not.toBeInTheDocument();
    });

    expect(screen.getByRole('combobox')).not.toBeDisabled();
  });

  test('does not change when same layout is selected', () => {
    const consoleSpy = vi.spyOn(console, 'warn').mockImplementation(() => {});
    
    renderWithProvider(<LayoutSwitcher />);

    const select = screen.getByRole('combobox');
    
    // Try to select the same layout
    fireEvent.change(select, { target: { value: 'overview' } });

    // Should not show transition indicator
    expect(screen.queryByText('Switching...')).not.toBeInTheDocument();
    
    consoleSpy.mockRestore();
  });

  test('handles rapid layout changes', async () => {
    renderWithProvider(<LayoutSwitcher />);

    const select = screen.getByRole('combobox');
    
    // Rapidly change layouts
    fireEvent.change(select, { target: { value: 'detailed' } });
    fireEvent.change(select, { target: { value: 'mobile' } });
    fireEvent.change(select, { target: { value: 'compact' } });

    // Wait for final transition
    await waitFor(() => {
      expect(select).toHaveValue('compact');
    });

    expect(localStorage.getItem('dashboard-layout')).toBe('compact');
  });
});

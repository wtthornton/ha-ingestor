import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { ChartFilter } from '../../src/components/ChartFilter';
import { ChartFilters } from '../../src/components/InteractiveChart';

// Mock date-fns
vi.mock('date-fns', () => ({
  format: (date: Date, format: string) => {
    if (format === "yyyy-MM-dd'T'HH:mm") {
      return '2024-01-01T12:00';
    }
    return '2024-01-01';
  },
  subDays: (date: Date, days: number) => new Date('2024-01-01'),
  subHours: (date: Date, hours: number) => new Date('2024-01-01'),
  subWeeks: (date: Date, weeks: number) => new Date('2024-01-01'),
  subMonths: (date: Date, months: number) => new Date('2024-01-01'),
}));

describe('ChartFilter', () => {
  const defaultProps = {
    filters: {} as ChartFilters,
    onFilterChange: vi.fn(),
    chartType: 'line' as const,
  };

  test('renders filter toggle button', () => {
    render(<ChartFilter {...defaultProps} />);

    expect(screen.getByText('Filters')).toBeInTheDocument();
  });

  test('expands filter content when clicked', () => {
    render(<ChartFilter {...defaultProps} />);

    const toggleButton = screen.getByText('Filters');
    fireEvent.click(toggleButton);

    expect(screen.getByText('Quick Time Range')).toBeInTheDocument();
    expect(screen.getByText('Last Hour')).toBeInTheDocument();
  });

  test('collapses filter content when clicked again', () => {
    render(<ChartFilter {...defaultProps} />);

    const toggleButton = screen.getByText('Filters');
    
    // Expand
    fireEvent.click(toggleButton);
    expect(screen.getByText('Quick Time Range')).toBeInTheDocument();
    
    // Collapse
    fireEvent.click(toggleButton);
    expect(screen.queryByText('Quick Time Range')).not.toBeInTheDocument();
  });

  test('shows active filter indicator when filters are applied', () => {
    const filtersWithTimeRange: ChartFilters = {
      timeRange: {
        start: new Date('2024-01-01'),
        end: new Date('2024-01-02'),
      },
    };

    render(<ChartFilter {...defaultProps} filters={filtersWithTimeRange} />);

    expect(screen.getByText('Active')).toBeInTheDocument();
  });

  test('handles time range preset selection', async () => {
    // Mock the current date to be consistent
    const mockDate = new Date('2024-01-01T12:00:00Z');
    vi.setSystemTime(mockDate);
    
    render(<ChartFilter {...defaultProps} />);

    // Expand filters
    fireEvent.click(screen.getByText('Filters'));
    
    // Click on a preset
    fireEvent.click(screen.getByText('Last Hour'));

    await waitFor(() => {
      expect(defaultProps.onFilterChange).toHaveBeenCalledWith({
        timeRange: {
          start: new Date('2024-01-01T11:00:00Z'), // 1 hour ago
          end: new Date('2024-01-01T12:00:00Z'),   // now
        },
      });
    });
    
    // Restore real time
    vi.useRealTimers();
  });

  test('handles custom time range input', async () => {
    render(<ChartFilter {...defaultProps} />);

    // Expand filters
    fireEvent.click(screen.getByText('Filters'));
    
    // Set custom start date
    const startInput = screen.getByLabelText('Start Date');
    fireEvent.change(startInput, { target: { value: '2024-01-01T10:00' } });

    await waitFor(() => {
      expect(defaultProps.onFilterChange).toHaveBeenCalledWith({
        timeRange: {
          start: new Date('2024-01-01T10:00'),
          end: undefined,
        },
      });
    });
  });

  test('handles entity type selection for line charts', async () => {
    render(<ChartFilter {...defaultProps} chartType="line" />);

    // Expand filters
    fireEvent.click(screen.getByText('Filters'));
    
    // Click on an entity type
    fireEvent.click(screen.getByText('sensor'));

    await waitFor(() => {
      expect(defaultProps.onFilterChange).toHaveBeenCalledWith({
        entityTypes: ['sensor'],
      });
    });
  });

  test('handles entity type deselection', async () => {
    const filtersWithEntityTypes: ChartFilters = {
      entityTypes: ['sensor', 'switch'],
    };

    render(<ChartFilter {...defaultProps} filters={filtersWithEntityTypes} chartType="line" />);

    // Expand filters
    fireEvent.click(screen.getByText('Filters'));
    
    // Click on an already selected entity type
    fireEvent.click(screen.getByText('sensor'));

    await waitFor(() => {
      expect(defaultProps.onFilterChange).toHaveBeenCalledWith({
        entityTypes: ['switch'],
      });
    });
  });

  test('handles event type selection', async () => {
    render(<ChartFilter {...defaultProps} />);

    // Expand filters
    fireEvent.click(screen.getByText('Filters'));
    
    // Click on an event type
    fireEvent.click(screen.getByText('state_changed'));

    await waitFor(() => {
      expect(defaultProps.onFilterChange).toHaveBeenCalledWith({
        eventTypes: ['state_changed'],
      });
    });
  });

  test('handles data points limit change', async () => {
    render(<ChartFilter {...defaultProps} />);

    // Expand filters
    fireEvent.click(screen.getByText('Filters'));
    
    // Set data points limit
    const dataPointsInput = screen.getByPlaceholderText('e.g., 1000');
    fireEvent.change(dataPointsInput, { target: { value: '1000' } });

    await waitFor(() => {
      expect(defaultProps.onFilterChange).toHaveBeenCalledWith({
        dataPoints: 1000,
      });
    });
  });

  test('clears all filters when clear button is clicked', () => {
    const filtersWithData: ChartFilters = {
      timeRange: {
        start: new Date('2024-01-01'),
        end: new Date('2024-01-02'),
      },
      entityTypes: ['sensor'],
    };

    render(<ChartFilter {...defaultProps} filters={filtersWithData} />);

    // Click clear button
    fireEvent.click(screen.getByText('Clear All'));

    expect(defaultProps.onFilterChange).toHaveBeenCalledWith({});
  });

  test('shows correct styling for selected filters', () => {
    const filtersWithEntityTypes: ChartFilters = {
      entityTypes: ['sensor'],
    };

    render(<ChartFilter {...defaultProps} filters={filtersWithEntityTypes} chartType="line" />);

    // Expand filters
    fireEvent.click(screen.getByText('Filters'));
    
    const sensorButton = screen.getByText('sensor');
    expect(sensorButton).toHaveClass('bg-green-100', 'text-green-800', 'border-green-300');
  });

  test('does not show entity types for pie charts', () => {
    render(<ChartFilter {...defaultProps} chartType="pie" />);

    // Expand filters
    fireEvent.click(screen.getByText('Filters'));
    
    expect(screen.queryByText('Entity Types')).not.toBeInTheDocument();
  });

  test('shows help text for data points input', () => {
    render(<ChartFilter {...defaultProps} />);

    // Expand filters
    fireEvent.click(screen.getByText('Filters'));
    
    expect(screen.getByText('Limit the number of data points for better performance')).toBeInTheDocument();
  });
});

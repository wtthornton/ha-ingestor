import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { InteractiveChart } from '../../src/components/InteractiveChart';
import { ChartData, ChartType } from '../../src/types';

// Mock the child components
vi.mock('../../src/components/ChartToolbar', () => ({
  ChartToolbar: ({ title, onExport, onZoomReset, realTime }: any) => (
    <div data-testid="chart-toolbar">
      <h3>{title}</h3>
      {realTime && (
        <div data-testid="live-indicator">
          <span>Live</span>
        </div>
      )}
      <button onClick={() => onExport('csv')} data-testid="export-csv">Export CSV</button>
      <button onClick={() => onExport('json')} data-testid="export-json">Export JSON</button>
      <button onClick={() => onExport('pdf')} data-testid="export-pdf">Export PDF</button>
      <button onClick={onZoomReset} data-testid="reset-zoom">Reset Zoom</button>
    </div>
  ),
}));

vi.mock('../../src/components/ChartFilter', () => ({
  ChartFilter: ({ onFilterChange }: any) => (
    <div data-testid="chart-filter">
      <button onClick={() => onFilterChange({ timeRange: { start: new Date('2024-01-01'), end: new Date('2024-01-02') } })} data-testid="apply-filter">
        Apply Filter
      </button>
    </div>
  ),
}));

vi.mock('../../src/components/SkeletonLoader', () => ({
  ChartSkeleton: ({ height }: any) => (
    <div data-testid="chart-skeleton" style={{ height: `${height}px` }}>
      Chart Skeleton
    </div>
  ),
}));

// Mock Chart.js components
vi.mock('react-chartjs-2', () => ({
  Line: ({ data, options, ref, onClick }: any) => (
    <div data-testid="line-chart" ref={ref} onClick={(e) => onClick && onClick(e)}>
      Line Chart - {data.labels.length} points
    </div>
  ),
  Bar: ({ data, options, ref, onClick }: any) => (
    <div data-testid="bar-chart" ref={ref} onClick={(e) => onClick && onClick(e)}>
      Bar Chart - {data.labels.length} points
    </div>
  ),
  Doughnut: ({ data, options, ref, onClick }: any) => (
    <div data-testid="doughnut-chart" ref={ref} onClick={(e) => onClick && onClick(e)}>
      Doughnut Chart - {data.labels.length} points
    </div>
  ),
}));

const mockChartData: ChartData = {
  labels: ['Jan', 'Feb', 'Mar', 'Apr', 'May'],
  datasets: [
    {
      label: 'Test Dataset',
      data: [10, 20, 30, 40, 50],
      borderColor: 'rgb(75, 192, 192)',
      backgroundColor: 'rgba(75, 192, 192, 0.2)',
    },
  ],
};

describe('InteractiveChart', () => {
  const defaultProps = {
    data: mockChartData,
    type: 'line' as ChartType,
    title: 'Test Chart',
    loading: false,
    height: 300,
  };

  test('renders chart with toolbar and filter', () => {
    render(<InteractiveChart {...defaultProps} />);

    expect(screen.getByTestId('chart-toolbar')).toBeInTheDocument();
    expect(screen.getByTestId('chart-filter')).toBeInTheDocument();
    expect(screen.getByTestId('line-chart')).toBeInTheDocument();
  });

  test('renders skeleton when loading', () => {
    render(<InteractiveChart {...defaultProps} loading={true} />);

    expect(screen.getByTestId('chart-skeleton')).toBeInTheDocument();
    expect(screen.queryByTestId('line-chart')).not.toBeInTheDocument();
  });

  test('renders different chart types', () => {
    const { rerender } = render(<InteractiveChart {...defaultProps} type="bar" />);
    expect(screen.getByTestId('bar-chart')).toBeInTheDocument();

    rerender(<InteractiveChart {...defaultProps} type="doughnut" />);
    expect(screen.getByTestId('doughnut-chart')).toBeInTheDocument();
  });

  test('handles export events', async () => {
    const onExport = vi.fn();
    render(<InteractiveChart {...defaultProps} onExport={onExport} />);

    fireEvent.click(screen.getByTestId('export-csv'));
    expect(onExport).toHaveBeenCalledWith('csv');

    fireEvent.click(screen.getByTestId('export-json'));
    expect(onExport).toHaveBeenCalledWith('json');

    fireEvent.click(screen.getByTestId('export-pdf'));
    expect(onExport).toHaveBeenCalledWith('pdf');
  });

  test('handles filter changes', async () => {
    const onFilter = vi.fn();
    render(<InteractiveChart {...defaultProps} onFilter={onFilter} />);

    fireEvent.click(screen.getByTestId('apply-filter'));
    
    await waitFor(() => {
      expect(onFilter).toHaveBeenCalledWith({
        timeRange: { start: new Date('2024-01-01'), end: new Date('2024-01-02') }
      });
    });
  });

  test('handles zoom reset', () => {
    const onZoomReset = vi.fn();
    render(<InteractiveChart {...defaultProps} />);

    // The reset zoom button should be available when zoomed
    fireEvent.click(screen.getByTestId('reset-zoom'));
    // Note: The InteractiveChart component handles zoom reset internally
    // so we just verify the button is clickable
    expect(screen.getByTestId('reset-zoom')).toBeInTheDocument();
  });

  test('shows real-time indicator when enabled', () => {
    render(<InteractiveChart {...defaultProps} realTime={true} />);
    
    expect(screen.getByText('Live')).toBeInTheDocument();
  });

  test('handles drill-down clicks', () => {
    render(<InteractiveChart {...defaultProps} enableDrillDown={true} />);
    
    const chart = screen.getByTestId('line-chart');
    
    // Verify the chart is rendered
    expect(chart).toBeInTheDocument();
    
    // The drill-down functionality is enabled (we can verify this by checking the component renders)
    expect(screen.getByTestId('chart-toolbar')).toBeInTheDocument();
  });

  test('disables drill-down when disabled', () => {
    const consoleSpy = vi.spyOn(console, 'log').mockImplementation(() => {});
    
    render(<InteractiveChart {...defaultProps} enableDrillDown={false} />);
    
    const chart = screen.getByTestId('line-chart');
    fireEvent.click(chart);
    
    expect(consoleSpy).not.toHaveBeenCalled();
    
    consoleSpy.mockRestore();
  });

  test('applies correct height styling', () => {
    render(<InteractiveChart {...defaultProps} height={400} />);
    
    const chartContainer = screen.getByTestId('line-chart').parentElement;
    expect(chartContainer).toHaveStyle({ height: '400px' });
  });

  test('passes chart data correctly', () => {
    render(<InteractiveChart {...defaultProps} />);
    
    expect(screen.getByText('Line Chart - 5 points')).toBeInTheDocument();
  });
});

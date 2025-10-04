import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import { ChartToolbar } from '../../src/components/ChartToolbar';

describe('ChartToolbar', () => {
  const defaultProps = {
    title: 'Test Chart',
    isZoomed: false,
    onZoomReset: vi.fn(),
    onExport: vi.fn(),
  };

  test('renders title and export buttons', () => {
    render(<ChartToolbar {...defaultProps} />);

    expect(screen.getByText('Test Chart')).toBeInTheDocument();
    expect(screen.getByText('CSV')).toBeInTheDocument();
    expect(screen.getByText('JSON')).toBeInTheDocument();
    expect(screen.getByText('PDF')).toBeInTheDocument();
  });

  test('shows real-time indicator when enabled', () => {
    render(<ChartToolbar {...defaultProps} realTime={true} />);

    expect(screen.getByText('Live')).toBeInTheDocument();
  });

  test('hides real-time indicator when disabled', () => {
    render(<ChartToolbar {...defaultProps} realTime={false} />);

    expect(screen.queryByText('Live')).not.toBeInTheDocument();
  });

  test('shows reset zoom button when zoomed', () => {
    render(<ChartToolbar {...defaultProps} isZoomed={true} />);

    expect(screen.getByText('Reset Zoom')).toBeInTheDocument();
  });

  test('hides reset zoom button when not zoomed', () => {
    render(<ChartToolbar {...defaultProps} isZoomed={false} />);

    expect(screen.queryByText('Reset Zoom')).not.toBeInTheDocument();
  });

  test('handles export button clicks', () => {
    const onExport = vi.fn();
    render(<ChartToolbar {...defaultProps} onExport={onExport} />);

    fireEvent.click(screen.getByText('CSV'));
    expect(onExport).toHaveBeenCalledWith('csv');

    fireEvent.click(screen.getByText('JSON'));
    expect(onExport).toHaveBeenCalledWith('json');

    fireEvent.click(screen.getByText('PDF'));
    expect(onExport).toHaveBeenCalledWith('pdf');
  });

  test('handles zoom reset click', () => {
    const onZoomReset = vi.fn();
    render(<ChartToolbar {...defaultProps} isZoomed={true} onZoomReset={onZoomReset} />);

    fireEvent.click(screen.getByText('Reset Zoom'));
    expect(onZoomReset).toHaveBeenCalled();
  });

  test('shows zoom and pan status', () => {
    render(<ChartToolbar {...defaultProps} enableZoom={true} enablePan={true} />);

    expect(screen.getByText('Zoom & Pan')).toBeInTheDocument();
  });

  test('shows zoom only status when pan disabled', () => {
    render(<ChartToolbar {...defaultProps} enableZoom={true} enablePan={false} />);

    expect(screen.getByText('Zoom only')).toBeInTheDocument();
  });

  test('shows drill-down instruction when enabled', () => {
    render(<ChartToolbar {...defaultProps} enableDrillDown={true} />);

    expect(screen.getByText('Click to drill down')).toBeInTheDocument();
  });

  test('hides drill-down instruction when disabled', () => {
    render(<ChartToolbar {...defaultProps} enableDrillDown={false} />);

    expect(screen.queryByText('Click to drill down')).not.toBeInTheDocument();
  });

  test('applies correct styling to buttons', () => {
    render(<ChartToolbar {...defaultProps} />);

    const csvButton = screen.getByText('CSV');
    expect(csvButton).toHaveClass('px-3', 'py-1', 'text-xs', 'font-medium');
  });

  test('applies correct styling to reset zoom button', () => {
    render(<ChartToolbar {...defaultProps} isZoomed={true} />);

    const resetButton = screen.getByText('Reset Zoom');
    expect(resetButton).toHaveClass('px-3', 'py-1', 'text-xs', 'font-medium');
  });
});

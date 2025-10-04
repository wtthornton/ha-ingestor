import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { ExportHistory } from '../../src/components/ExportHistory';
import { ThemeProvider } from '../../src/contexts/ThemeContext';

// Mock the ExportHistoryManager
const mockGetHistory = vi.fn();
const mockAddToHistory = vi.fn();
const mockRemoveFromHistory = vi.fn();
const mockClearHistory = vi.fn();

vi.mock('../../src/utils/exportUtils', () => ({
  ExportHistoryManager: {
    getHistory: mockGetHistory,
    addToHistory: mockAddToHistory,
    removeFromHistory: mockRemoveFromHistory,
    clearHistory: mockClearHistory,
  },
}));

const mockHistoryItems = [
  {
    id: 'export-1',
    filename: 'events-2024-01-01.csv',
    format: 'csv',
    timestamp: new Date('2024-01-01T10:00:00Z'),
    size: 1000,
    status: 'completed' as const,
    options: {
      title: 'Events Export',
      includeMetadata: true,
    },
  },
  {
    id: 'export-2',
    filename: 'analysis-2024-01-02.json',
    format: 'json',
    timestamp: new Date('2024-01-02T15:30:00Z'),
    size: 500,
    status: 'completed' as const,
    options: {
      title: 'Historical Analysis',
      includeMetadata: false,
    },
  },
  {
    id: 'export-3',
    filename: 'failed-export.xlsx',
    format: 'excel',
    timestamp: new Date('2024-01-03T09:15:00Z'),
    size: 0,
    status: 'failed' as const,
    options: {},
  },
];

const renderWithTheme = (component: React.ReactElement) => {
  return render(
    <ThemeProvider>
      {component}
    </ThemeProvider>
  );
};

describe('ExportHistory', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('should render empty state when no history exists', () => {
    mockGetHistory.mockReturnValue([]);

    renderWithTheme(<ExportHistory />);

    expect(screen.getByText('No export history')).toBeInTheDocument();
    expect(screen.getByText('Your export history will appear here once you start exporting data.')).toBeInTheDocument();
  });

  it('should render export history items', () => {
    mockGetHistory.mockReturnValue(mockHistoryItems);

    renderWithTheme(<ExportHistory />);

    expect(screen.getByText('Export History')).toBeInTheDocument();
    expect(screen.getByText('events-2024-01-01.csv')).toBeInTheDocument();
    expect(screen.getByText('analysis-2024-01-02.json')).toBeInTheDocument();
    expect(screen.getByText('failed-export.xlsx')).toBeInTheDocument();
  });

  it('should display export item details', () => {
    mockGetHistory.mockReturnValue(mockHistoryItems);

    renderWithTheme(<ExportHistory />);

    // Check for format badges
    expect(screen.getAllByText('CSV')).toHaveLength(1);
    expect(screen.getAllByText('JSON')).toHaveLength(1);
    expect(screen.getAllByText('EXCEL')).toHaveLength(1);

    // Check for status badges
    expect(screen.getAllByText('completed')).toHaveLength(2);
    expect(screen.getByText('failed')).toBeInTheDocument();

    // Check for file sizes
    expect(screen.getByText('195.31 KB')).toBeInTheDocument(); // 1000 * 200 bytes
    expect(screen.getByText('97.66 KB')).toBeInTheDocument(); // 500 * 200 bytes
  });

  it('should allow selecting individual items', () => {
    mockGetHistory.mockReturnValue(mockHistoryItems);

    renderWithTheme(<ExportHistory />);

    const checkboxes = screen.getAllByRole('checkbox');
    expect(checkboxes).toHaveLength(4); // 3 items + select all

    // Select first item
    fireEvent.click(checkboxes[1]); // Skip select all checkbox
    expect(checkboxes[1]).toBeChecked();
  });

  it('should allow selecting all items', () => {
    mockGetHistory.mockReturnValue(mockHistoryItems);

    renderWithTheme(<ExportHistory />);

    const selectAllCheckbox = screen.getByLabelText(/Select All/);
    fireEvent.click(selectAllCheckbox);

    const itemCheckboxes = screen.getAllByRole('checkbox');
    itemCheckboxes.forEach(checkbox => {
      expect(checkbox).toBeChecked();
    });
  });

  it('should show remove selected button when items are selected', () => {
    mockGetHistory.mockReturnValue(mockHistoryItems);

    renderWithTheme(<ExportHistory />);

    const selectAllCheckbox = screen.getByLabelText(/Select All/);
    fireEvent.click(selectAllCheckbox);

    expect(screen.getByText('Remove Selected (3)')).toBeInTheDocument();
  });

  it('should remove selected items', () => {
    mockGetHistory.mockReturnValue(mockHistoryItems);

    renderWithTheme(<ExportHistory />);

    // Select first item
    const checkboxes = screen.getAllByRole('checkbox');
    fireEvent.click(checkboxes[1]);

    // Click remove selected
    const removeButton = screen.getByText('Remove Selected (1)');
    fireEvent.click(removeButton);

    expect(mockRemoveFromHistory).toHaveBeenCalledWith('export-1');
  });

  it('should remove individual item', () => {
    mockGetHistory.mockReturnValue(mockHistoryItems);

    renderWithTheme(<ExportHistory />);

    const removeButtons = screen.getAllByRole('button', { name: /remove/i });
    fireEvent.click(removeButtons[0]); // Remove first item

    expect(mockRemoveFromHistory).toHaveBeenCalledWith('export-1');
  });

  it('should clear all history', () => {
    mockGetHistory.mockReturnValue(mockHistoryItems);

    renderWithTheme(<ExportHistory />);

    const clearAllButton = screen.getByText('Clear All');
    fireEvent.click(clearAllButton);

    expect(mockClearHistory).toHaveBeenCalled();
  });

  it('should display export count and total size', () => {
    mockGetHistory.mockReturnValue(mockHistoryItems);

    renderWithTheme(<ExportHistory />);

    expect(screen.getByText('Showing 3 exports')).toBeInTheDocument();
    expect(screen.getByText('Total size: 292.97 KB')).toBeInTheDocument();
  });

  it('should show correct format icons', () => {
    mockGetHistory.mockReturnValue(mockHistoryItems);

    renderWithTheme(<ExportHistory />);

    // Check that format icons are present (they're SVG elements)
    const formatIcons = screen.getAllByTestId(/format-icon|document-icon/);
    expect(formatIcons.length).toBeGreaterThan(0);
  });

  it('should handle empty history gracefully', () => {
    mockGetHistory.mockReturnValue([]);

    renderWithTheme(<ExportHistory />);

    expect(screen.getByText('No export history')).toBeInTheDocument();
    expect(screen.queryByText('Clear All')).not.toBeInTheDocument();
  });

  it('should update when history changes', () => {
    mockGetHistory.mockReturnValue([]);

    const { rerender } = renderWithTheme(<ExportHistory />);

    expect(screen.getByText('No export history')).toBeInTheDocument();

    // Update history
    mockGetHistory.mockReturnValue([mockHistoryItems[0]]);
    rerender(
      <ThemeProvider>
        <ExportHistory />
      </ThemeProvider>
    );

    expect(screen.getByText('events-2024-01-01.csv')).toBeInTheDocument();
  });

  it('should display export titles when available', () => {
    mockGetHistory.mockReturnValue(mockHistoryItems);

    renderWithTheme(<ExportHistory />);

    expect(screen.getByText('Events Export')).toBeInTheDocument();
    expect(screen.getByText('Historical Analysis')).toBeInTheDocument();
  });

  it('should handle different status types correctly', () => {
    const mixedStatusItems = [
      {
        id: 'export-1',
        filename: 'completed.csv',
        format: 'csv',
        timestamp: new Date('2024-01-01'),
        size: 100,
        status: 'completed' as const,
        options: {},
      },
      {
        id: 'export-2',
        filename: 'processing.json',
        format: 'json',
        timestamp: new Date('2024-01-02'),
        size: 50,
        status: 'processing' as const,
        options: {},
      },
      {
        id: 'export-3',
        filename: 'failed.xlsx',
        format: 'excel',
        timestamp: new Date('2024-01-03'),
        size: 0,
        status: 'failed' as const,
        options: {},
      },
    ];

    mockGetHistory.mockReturnValue(mixedStatusItems);

    renderWithTheme(<ExportHistory />);

    expect(screen.getByText('completed')).toBeInTheDocument();
    expect(screen.getByText('processing')).toBeInTheDocument();
    expect(screen.getByText('failed')).toBeInTheDocument();
  });
});

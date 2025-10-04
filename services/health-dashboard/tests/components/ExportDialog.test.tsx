import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { ExportDialog } from '../../src/components/ExportDialog';
import { EventData } from '../../src/types';
import { ThemeProvider } from '../../src/contexts/ThemeContext';

// Mock the export utilities
vi.mock('../../src/utils/exportUtils', () => ({
  exportEventsToCSV: vi.fn(() => ({
    success: true,
    filename: 'test.csv',
    progress: 100,
  })),
  exportEventsToJSON: vi.fn(() => ({
    success: true,
    filename: 'test.json',
    progress: 100,
  })),
  exportEventsToExcel: vi.fn(() => ({
    success: true,
    filename: 'test.xlsx',
    progress: 100,
  })),
  performHistoricalAnalysis: vi.fn(() => ({
    labels: ['2024-01-01', '2024-01-02'],
    datasets: [{ label: 'event_count', data: [10, 15] }],
  })),
  ExportHistoryManager: {
    addToHistory: vi.fn(),
  },
}));

const mockEvents: EventData[] = [
  {
    id: '1',
    timestamp: '2024-01-01T00:00:00Z',
    entity_id: 'sensor.temperature',
    event_type: 'state_changed',
    new_state: { state: '20.5' },
    attributes: { unit_of_measurement: '°C' },
    domain: 'sensor',
    service: null,
    context: { id: 'context-1' },
  },
  {
    id: '2',
    timestamp: '2024-01-01T01:00:00Z',
    entity_id: 'sensor.humidity',
    event_type: 'state_changed',
    new_state: { state: '65' },
    attributes: { unit_of_measurement: '%' },
    domain: 'sensor',
    service: null,
    context: { id: 'context-2' },
  },
];

const renderWithTheme = (component: React.ReactElement) => {
  return render(
    <ThemeProvider>
      {component}
    </ThemeProvider>
  );
};

describe('ExportDialog', () => {
  const mockOnClose = vi.fn();
  const mockOnExportComplete = vi.fn();

  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('should not render when isOpen is false', () => {
    renderWithTheme(
      <ExportDialog
        isOpen={false}
        onClose={mockOnClose}
        events={mockEvents}
        onExportComplete={mockOnExportComplete}
      />
    );

    expect(screen.queryByText('Export Data')).not.toBeInTheDocument();
  });

  it('should render when isOpen is true', () => {
    renderWithTheme(
      <ExportDialog
        isOpen={true}
        onClose={mockOnClose}
        events={mockEvents}
        onExportComplete={mockOnExportComplete}
      />
    );

    expect(screen.getByText('Export Data')).toBeInTheDocument();
    expect(screen.getByText('Export Summary')).toBeInTheDocument();
    expect(screen.getByText('Export Format')).toBeInTheDocument();
    expect(screen.getByText('Export Options')).toBeInTheDocument();
  });

  it('should display export summary with event count', () => {
    renderWithTheme(
      <ExportDialog
        isOpen={true}
        onClose={mockOnClose}
        events={mockEvents}
        onExportComplete={mockOnExportComplete}
      />
    );

    expect(screen.getByText('Total Events: 2')).toBeInTheDocument();
  });

  it('should allow format selection', () => {
    renderWithTheme(
      <ExportDialog
        isOpen={true}
        onClose={mockOnClose}
        events={mockEvents}
        onExportComplete={mockOnExportComplete}
      />
    );

    // Check that all format options are present
    expect(screen.getByText('CSV')).toBeInTheDocument();
    expect(screen.getByText('JSON')).toBeInTheDocument();
    expect(screen.getByText('Excel')).toBeInTheDocument();
    expect(screen.getByText('PDF')).toBeInTheDocument();
  });

  it('should allow filename customization', () => {
    renderWithTheme(
      <ExportDialog
        isOpen={true}
        onClose={mockOnClose}
        events={mockEvents}
        onExportComplete={mockOnExportComplete}
      />
    );

    const filenameInput = screen.getByDisplayValue(/events-export-/);
    expect(filenameInput).toBeInTheDocument();

    fireEvent.change(filenameInput, { target: { value: 'custom-export' } });
    expect(filenameInput).toHaveValue('custom-export');
  });

  it('should allow title customization', () => {
    renderWithTheme(
      <ExportDialog
        isOpen={true}
        onClose={mockOnClose}
        events={mockEvents}
        onExportComplete={mockOnExportComplete}
      />
    );

    const titleInput = screen.getByDisplayValue('Events Export');
    expect(titleInput).toBeInTheDocument();

    fireEvent.change(titleInput, { target: { value: 'Custom Title' } });
    expect(titleInput).toHaveValue('Custom Title');
  });

  it('should toggle metadata inclusion', () => {
    renderWithTheme(
      <ExportDialog
        isOpen={true}
        onClose={mockOnClose}
        events={mockEvents}
        onExportComplete={mockOnExportComplete}
      />
    );

    const metadataCheckbox = screen.getByLabelText(/Include metadata/);
    expect(metadataCheckbox).toBeChecked();

    fireEvent.click(metadataCheckbox);
    expect(metadataCheckbox).not.toBeChecked();
  });

  it('should show advanced options when toggled', () => {
    renderWithTheme(
      <ExportDialog
        isOpen={true}
        onClose={mockOnClose}
        events={mockEvents}
        onExportComplete={mockOnExportComplete}
      />
    );

    const advancedButton = screen.getByText(/Show.*Historical Analysis Options/);
    fireEvent.click(advancedButton);

    expect(screen.getByText('Aggregation Period')).toBeInTheDocument();
    expect(screen.getByText('Analysis Time Range')).toBeInTheDocument();
  });

  it('should handle export with CSV format', async () => {
    renderWithTheme(
      <ExportDialog
        isOpen={true}
        onClose={mockOnClose}
        events={mockEvents}
        onExportComplete={mockOnExportComplete}
      />
    );

    const exportButton = screen.getByText('Export Data');
    fireEvent.click(exportButton);

    await waitFor(() => {
      expect(mockOnExportComplete).toHaveBeenCalledWith({
        success: true,
        filename: 'test.csv',
        progress: 100,
      });
    });
  });

  it('should handle export with JSON format', async () => {
    renderWithTheme(
      <ExportDialog
        isOpen={true}
        onClose={mockOnClose}
        events={mockEvents}
        onExportComplete={mockOnExportComplete}
      />
    );

    // Select JSON format
    const jsonOption = screen.getByText('JSON');
    fireEvent.click(jsonOption);

    const exportButton = screen.getByText('Export Data');
    fireEvent.click(exportButton);

    await waitFor(() => {
      expect(mockOnExportComplete).toHaveBeenCalledWith({
        success: true,
        filename: 'test.json',
        progress: 100,
      });
    });
  });

  it('should handle export with Excel format', async () => {
    renderWithTheme(
      <ExportDialog
        isOpen={true}
        onClose={mockOnClose}
        events={mockEvents}
        onExportComplete={mockOnExportComplete}
      />
    );

    // Select Excel format
    const excelOption = screen.getByText('Excel');
    fireEvent.click(excelOption);

    const exportButton = screen.getByText('Export Data');
    fireEvent.click(exportButton);

    await waitFor(() => {
      expect(mockOnExportComplete).toHaveBeenCalledWith({
        success: true,
        filename: 'test.xlsx',
        progress: 100,
      });
    });
  });

  it('should handle historical analysis export', async () => {
    renderWithTheme(
      <ExportDialog
        isOpen={true}
        onClose={mockOnClose}
        events={mockEvents}
        onExportComplete={mockOnExportComplete}
      />
    );

    // Show advanced options
    const advancedButton = screen.getByText(/Show.*Historical Analysis Options/);
    fireEvent.click(advancedButton);

    // Click export analysis button
    const analysisButton = screen.getByText('Export Analysis');
    fireEvent.click(analysisButton);

    await waitFor(() => {
      expect(mockOnExportComplete).toHaveBeenCalled();
    });
  });

  it('should disable export button when no events', () => {
    renderWithTheme(
      <ExportDialog
        isOpen={true}
        onClose={mockOnClose}
        events={[]}
        onExportComplete={mockOnExportComplete}
      />
    );

    const exportButton = screen.getByText('Export Data');
    expect(exportButton).toBeDisabled();
  });

  it('should show progress during export', async () => {
    renderWithTheme(
      <ExportDialog
        isOpen={true}
        onClose={mockOnClose}
        events={mockEvents}
        onExportComplete={mockOnExportComplete}
      />
    );

    const exportButton = screen.getByText('Export Data');
    fireEvent.click(exportButton);

    // Should show progress
    await waitFor(() => {
      expect(screen.getByText('Exporting...')).toBeInTheDocument();
    });
  });

  it('should close dialog when cancel is clicked', () => {
    renderWithTheme(
      <ExportDialog
        isOpen={true}
        onClose={mockOnClose}
        events={mockEvents}
        onExportComplete={mockOnExportComplete}
      />
    );

    const cancelButton = screen.getByText('Cancel');
    fireEvent.click(cancelButton);

    expect(mockOnClose).toHaveBeenCalled();
  });

  it('should close dialog when backdrop is clicked', () => {
    renderWithTheme(
      <ExportDialog
        isOpen={true}
        onClose={mockOnClose}
        events={mockEvents}
        onExportComplete={mockOnExportComplete}
      />
    );

    const backdrop = screen.getByRole('dialog').parentElement;
    fireEvent.click(backdrop!);

    expect(mockOnClose).toHaveBeenCalled();
  });

  it('should handle export errors gracefully', async () => {
    // Mock export function to throw error
    const { exportEventsToCSV } = await import('../../src/utils/exportUtils');
    vi.mocked(exportEventsToCSV).mockImplementation(() => ({
      success: false,
      error: 'Export failed',
    }));

    renderWithTheme(
      <ExportDialog
        isOpen={true}
        onClose={mockOnClose}
        events={mockEvents}
        onExportComplete={mockOnExportComplete}
      />
    );

    const exportButton = screen.getByText('Export Data');
    fireEvent.click(exportButton);

    await waitFor(() => {
      expect(mockOnExportComplete).toHaveBeenCalledWith({
        success: false,
        error: 'Export failed',
      });
    });
  });
});

import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { ConfigurationViewer } from '../../src/components/ConfigurationViewer';
import { apiService } from '../../src/services/api';

// Mock the API service
jest.mock('../../src/services/api');
const mockApiService = apiService as jest.Mocked<typeof apiService>;

const mockConfiguration: any = {
  home_assistant_url: 'http://localhost:8123',
  home_assistant_token: 'secret-token',
  influxdb_url: 'http://localhost:8086',
  influxdb_token: 'influx-token',
  log_level: 'INFO',
  max_workers: 10,
  batch_size: 100,
};

describe('ConfigurationViewer', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    mockApiService.getConfiguration.mockResolvedValue(mockConfiguration);
  });

  it('renders configuration viewer correctly', async () => {
    render(<ConfigurationViewer service="websocket-ingestion" />);
    
    expect(screen.getByText('Configuration: websocket-ingestion')).toBeInTheDocument();
    expect(screen.getByText('Show Sensitive')).toBeInTheDocument();
    expect(screen.getByText('Edit')).toBeInTheDocument();
    expect(screen.getByText('Backup')).toBeInTheDocument();
    expect(screen.getByText('Restore')).toBeInTheDocument();
  });

  it('displays loading state initially', () => {
    render(<ConfigurationViewer service="websocket-ingestion" />);
    
    // Check for loading animation elements
    const loadingElements = document.querySelectorAll('.animate-pulse');
    expect(loadingElements.length).toBeGreaterThan(0);
  });

  it('fetches and displays configuration data', async () => {
    render(<ConfigurationViewer service="websocket-ingestion" />);
    
    await waitFor(() => {
      expect(mockApiService.getConfiguration).toHaveBeenCalledWith(false);
    });

    expect(screen.getByText('Home Assistant')).toBeInTheDocument();
    expect(screen.getByText('InfluxDB')).toBeInTheDocument();
    expect(screen.getByText('Logging')).toBeInTheDocument();
    expect(screen.getByText('Processing')).toBeInTheDocument();
  });

  it('masks sensitive data by default', async () => {
    render(<ConfigurationViewer service="websocket-ingestion" />);
    
    await waitFor(() => {
      expect(screen.getByText('home_assistant_token')).toBeInTheDocument();
    });

    // Sensitive fields should show masked values
    expect(screen.getByText('••••••••')).toBeInTheDocument();
  });

  it('shows sensitive data when toggle is clicked', async () => {
    render(<ConfigurationViewer service="websocket-ingestion" />);
    
    await waitFor(() => {
      expect(screen.getByText('Show Sensitive')).toBeInTheDocument();
    });

    fireEvent.click(screen.getByText('Show Sensitive'));

    await waitFor(() => {
      expect(mockApiService.getConfiguration).toHaveBeenCalledWith(true);
    });
  });

  it('expands and collapses configuration sections', async () => {
    render(<ConfigurationViewer service="websocket-ingestion" />);
    
    await waitFor(() => {
      expect(screen.getByText('Home Assistant')).toBeInTheDocument();
    });

    // Click to expand Home Assistant section
    fireEvent.click(screen.getByText('Home Assistant'));

    // Should show configuration fields
    expect(screen.getByText('home_assistant_url')).toBeInTheDocument();
    expect(screen.getByText('home_assistant_token')).toBeInTheDocument();
  });

  it('calls onEdit callback when Edit button is clicked', async () => {
    const mockOnEdit = jest.fn();
    render(<ConfigurationViewer service="websocket-ingestion" onEdit={mockOnEdit} />);
    
    await waitFor(() => {
      expect(screen.getByText('Edit')).toBeInTheDocument();
    });

    fireEvent.click(screen.getByText('Edit'));

    expect(mockOnEdit).toHaveBeenCalledWith(mockConfiguration);
  });

  it('calls onBackup callback when Backup button is clicked', async () => {
    const mockOnBackup = jest.fn();
    render(<ConfigurationViewer service="websocket-ingestion" onBackup={mockOnBackup} />);
    
    await waitFor(() => {
      expect(screen.getByText('Backup')).toBeInTheDocument();
    });

    fireEvent.click(screen.getByText('Backup'));

    expect(mockOnBackup).toHaveBeenCalledWith(mockConfiguration);
  });

  it('calls onRestore callback when Restore button is clicked', async () => {
    const mockOnRestore = jest.fn();
    render(<ConfigurationViewer service="websocket-ingestion" onRestore={mockOnRestore} />);
    
    await waitFor(() => {
      expect(screen.getByText('Restore')).toBeInTheDocument();
    });

    fireEvent.click(screen.getByText('Restore'));

    expect(mockOnRestore).toHaveBeenCalled();
  });

  it('displays error message when API call fails', async () => {
    mockApiService.getConfiguration.mockRejectedValue(new Error('API Error'));
    
    render(<ConfigurationViewer service="websocket-ingestion" />);
    
    await waitFor(() => {
      expect(screen.getByText('Configuration Error')).toBeInTheDocument();
    });

    expect(screen.getByText('API Error')).toBeInTheDocument();
    expect(screen.getByText('Retry')).toBeInTheDocument();
  });

  it('retries configuration fetch when Retry button is clicked', async () => {
    mockApiService.getConfiguration.mockRejectedValueOnce(new Error('API Error'));
    mockApiService.getConfiguration.mockResolvedValueOnce(mockConfiguration);
    
    render(<ConfigurationViewer service="websocket-ingestion" />);
    
    await waitFor(() => {
      expect(screen.getByText('Retry')).toBeInTheDocument();
    });

    fireEvent.click(screen.getByText('Retry'));

    await waitFor(() => {
      expect(mockApiService.getConfiguration).toHaveBeenCalledTimes(2);
    });
  });

  it('displays required field indicators', async () => {
    render(<ConfigurationViewer service="websocket-ingestion" />);
    
    await waitFor(() => {
      expect(screen.getByText('home_assistant_url')).toBeInTheDocument();
    });

    // Expand Home Assistant section
    fireEvent.click(screen.getByText('Home Assistant'));

    // Check for required field indicators
    const requiredIndicators = document.querySelectorAll('.text-red-500');
    expect(requiredIndicators.length).toBeGreaterThan(0);
  });

  it('displays sensitive field indicators', async () => {
    render(<ConfigurationViewer service="websocket-ingestion" />);
    
    await waitFor(() => {
      expect(screen.getByText('Home Assistant')).toBeInTheDocument();
    });

    // Expand Home Assistant section
    fireEvent.click(screen.getByText('Home Assistant'));

    // Check for sensitive field indicators
    const sensitiveIndicators = document.querySelectorAll('.text-orange-500');
    expect(sensitiveIndicators.length).toBeGreaterThan(0);
  });
});

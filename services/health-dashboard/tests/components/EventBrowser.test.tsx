import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { EventBrowser } from '../../src/components/EventBrowser';
import { apiService } from '../../src/services/api';

// Mock the API service
vi.mock('../../src/services/api');
const mockApiService = apiService as any;

const mockEvents = [
  {
    id: '1',
    timestamp: '2024-01-01T12:00:00Z',
    entity_id: 'sensor.temperature',
    event_type: 'state_changed',
    new_state: { state: '22.5', attributes: { unit_of_measurement: '°C' } },
    attributes: { temperature: 22.5 },
    tags: {},
  },
  {
    id: '2',
    timestamp: '2024-01-01T12:01:00Z',
    entity_id: 'binary_sensor.motion',
    event_type: 'state_changed',
    new_state: { state: 'on' },
    attributes: { motion: true },
    tags: {},
  },
];

const mockEntities = ['sensor.temperature', 'binary_sensor.motion'];
const mockEventTypes = ['state_changed', 'entity_registry_updated'];

describe('EventBrowser', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    mockApiService.getEvents.mockResolvedValue(mockEvents);
    mockApiService.getActiveEntities.mockResolvedValue(mockEntities);
    mockApiService.getEventTypes.mockResolvedValue(mockEventTypes);
    mockApiService.searchEvents.mockResolvedValue(mockEvents);
  });

  it('renders event browser correctly', async () => {
    render(<EventBrowser />);
    
    expect(screen.getByText('Event Browser')).toBeInTheDocument();
    expect(screen.getByText('Export CSV')).toBeInTheDocument();
    expect(screen.getByText('Export JSON')).toBeInTheDocument();
    
    await waitFor(() => {
      expect(screen.getByText('Entity ID')).toBeInTheDocument();
    });
  });

  it('displays loading state initially', () => {
    render(<EventBrowser />);
    
    // Check for loading spinner
    const loadingElements = document.querySelectorAll('.animate-spin');
    expect(loadingElements.length).toBeGreaterThan(0);
  });

  it('fetches and displays events', async () => {
    render(<EventBrowser />);
    
    await waitFor(() => {
      expect(mockApiService.getEvents).toHaveBeenCalled();
    });

    expect(screen.getByText('sensor.temperature')).toBeInTheDocument();
    expect(screen.getByText('binary_sensor.motion')).toBeInTheDocument();
  });

  it('handles entity filter selection', async () => {
    render(<EventBrowser />);
    
    await waitFor(() => {
      expect(screen.getByText('Entity ID')).toBeInTheDocument();
    });

    const entitySelect = screen.getByDisplayValue('All entities');
    fireEvent.change(entitySelect, { target: { value: 'sensor.temperature' } });

    await waitFor(() => {
      expect(mockApiService.getEvents).toHaveBeenCalledWith(
        expect.objectContaining({ entity_id: 'sensor.temperature' })
      );
    });
  });

  it('handles event type filter selection', async () => {
    render(<EventBrowser />);
    
    await waitFor(() => {
      expect(screen.getByText('Event Type')).toBeInTheDocument();
    });

    const typeSelect = screen.getByDisplayValue('All types');
    fireEvent.change(typeSelect, { target: { value: 'state_changed' } });

    await waitFor(() => {
      expect(mockApiService.getEvents).toHaveBeenCalledWith(
        expect.objectContaining({ event_type: 'state_changed' })
      );
    });
  });

  it('handles limit filter selection', async () => {
    render(<EventBrowser />);
    
    await waitFor(() => {
      expect(screen.getByText('Limit')).toBeInTheDocument();
    });

    const limitSelect = screen.getByDisplayValue('100');
    fireEvent.change(limitSelect, { target: { value: '500' } });

    await waitFor(() => {
      expect(mockApiService.getEvents).toHaveBeenCalledWith(
        expect.objectContaining({ limit: 500 })
      );
    });
  });

  it('handles time range filters', async () => {
    render(<EventBrowser />);
    
    await waitFor(() => {
      expect(screen.getByText('Start Time')).toBeInTheDocument();
    });

    const startTimeInput = screen.getByDisplayValue('');
    fireEvent.change(startTimeInput, { target: { value: '2024-01-01T10:00' } });

    await waitFor(() => {
      expect(mockApiService.getEvents).toHaveBeenCalledWith(
        expect.objectContaining({ start_time: '2024-01-01T10:00' })
      );
    });
  });

  it('handles search functionality', async () => {
    render(<EventBrowser />);
    
    await waitFor(() => {
      expect(screen.getByText('Search')).toBeInTheDocument();
    });

    const searchInput = screen.getByPlaceholderText(/Search events/);
    fireEvent.change(searchInput, { target: { value: 'temperature' } });
    fireEvent.keyPress(searchInput, { key: 'Enter', code: 'Enter' });

    await waitFor(() => {
      expect(mockApiService.searchEvents).toHaveBeenCalledWith('temperature');
    });
  });

  it('clears filters when Clear button is clicked', async () => {
    render(<EventBrowser />);
    
    await waitFor(() => {
      expect(screen.getByText('Clear')).toBeInTheDocument();
    });

    // Set some filters first
    const entitySelect = screen.getByDisplayValue('All entities');
    fireEvent.change(entitySelect, { target: { value: 'sensor.temperature' } });

    // Click clear
    fireEvent.click(screen.getByText('Clear'));

    await waitFor(() => {
      expect(mockApiService.getEvents).toHaveBeenCalledWith(
        expect.objectContaining({ entity_id: undefined })
      );
    });
  });

  it('calls onExport callback when export buttons are clicked', async () => {
    const mockOnExport = jest.fn();
    render(<EventBrowser onExport={mockOnExport} />);
    
    await waitFor(() => {
      expect(screen.getByText('Export CSV')).toBeInTheDocument();
    });

    fireEvent.click(screen.getByText('Export CSV'));
    expect(mockOnExport).toHaveBeenCalledWith(mockEvents, 'csv');

    fireEvent.click(screen.getByText('Export JSON'));
    expect(mockOnExport).toHaveBeenCalledWith(mockEvents, 'json');
  });

  it('displays error message when API call fails', async () => {
    mockApiService.getEvents.mockRejectedValue(new Error('API Error'));
    
    render(<EventBrowser />);
    
    await waitFor(() => {
      expect(screen.getByText('Query Error')).toBeInTheDocument();
    });

    expect(screen.getByText('API Error')).toBeInTheDocument();
  });

  it('displays query performance metrics', async () => {
    render(<EventBrowser />);
    
    await waitFor(() => {
      expect(screen.getByText(/events •/)).toBeInTheDocument();
    });

    // Should show performance metrics
    expect(screen.getByText(/ms/)).toBeInTheDocument();
  });

  it('filters events by search query', async () => {
    render(<EventBrowser />);
    
    await waitFor(() => {
      expect(screen.getByText('sensor.temperature')).toBeInTheDocument();
    });

    const searchInput = screen.getByPlaceholderText(/Search events/);
    fireEvent.change(searchInput, { target: { value: 'motion' } });

    // Should filter to show only motion-related events
    expect(screen.getByText('binary_sensor.motion')).toBeInTheDocument();
  });

  it('shows event details in expandable sections', async () => {
    render(<EventBrowser />);
    
    await waitFor(() => {
      expect(screen.getByText('sensor.temperature')).toBeInTheDocument();
    });

    // Check for attributes section
    expect(screen.getByText(/Attributes/)).toBeInTheDocument();
  });

  it('displays event timestamps in readable format', async () => {
    render(<EventBrowser />);
    
    await waitFor(() => {
      expect(screen.getByText(/Jan 01, 2024/)).toBeInTheDocument();
    });
  });

  it('shows state information for state_changed events', async () => {
    render(<EventBrowser />);
    
    await waitFor(() => {
      expect(screen.getByText('State:')).toBeInTheDocument();
    });

    expect(screen.getByText('22.5')).toBeInTheDocument();
    expect(screen.getByText('(°C)')).toBeInTheDocument();
  });
});

import { renderHook, waitFor } from '@testing-library/react';
import { useHealth } from '../../src/hooks/useHealth';
import { apiService } from '../../src/services/api';
import { websocketService } from '../../src/services/websocket';

// Mock the services
jest.mock('../../src/services/api');
jest.mock('../../src/services/websocket');

const mockApiService = apiService as jest.Mocked<typeof apiService>;
const mockWebsocketService = websocketService as jest.Mocked<typeof websocketService>;

describe('useHealth', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    
    // Mock API service
    mockApiService.getHealth.mockResolvedValue({
      overall_status: 'healthy',
      admin_api_status: 'running',
      ingestion_service: {
        status: 'healthy',
        websocket_connection: {
          is_connected: true,
          last_connection_time: '2024-01-01T12:00:00Z',
          connection_attempts: 5,
          last_error: null,
        },
        event_processing: {
          total_events: 1000,
          events_per_minute: 50,
          error_rate: 0.01,
        },
        weather_enrichment: {
          enabled: true,
          cache_hits: 100,
          api_calls: 10,
          last_error: null,
        },
        influxdb_storage: {
          is_connected: true,
          last_write_time: '2024-01-01T12:00:00Z',
          write_errors: 0,
        },
        timestamp: '2024-01-01T12:00:00Z',
      },
      timestamp: '2024-01-01T12:00:00Z',
    });

    // Mock WebSocket service
    mockWebsocketService.subscribe.mockReturnValue(() => {});
  });

  it('should fetch health data on mount', async () => {
    const { result } = renderHook(() => useHealth());

    expect(result.current.loading).toBe(true);
    expect(result.current.health).toBe(null);

    await waitFor(() => {
      expect(result.current.loading).toBe(false);
    });

    expect(result.current.health).toBeDefined();
    expect(result.current.health?.overall_status).toBe('healthy');
    expect(mockApiService.getHealth).toHaveBeenCalledTimes(1);
  });

  it('should handle API errors', async () => {
    const errorMessage = 'API Error';
    mockApiService.getHealth.mockRejectedValue(new Error(errorMessage));

    const { result } = renderHook(() => useHealth());

    await waitFor(() => {
      expect(result.current.loading).toBe(false);
    });

    expect(result.current.error).toBe(errorMessage);
    expect(result.current.health).toBe(null);
  });

  it('should refresh data when refresh is called', async () => {
    const { result } = renderHook(() => useHealth());

    await waitFor(() => {
      expect(result.current.loading).toBe(false);
    });

    // Call refresh
    result.current.refresh();

    expect(result.current.loading).toBe(true);
    await waitFor(() => {
      expect(result.current.loading).toBe(false);
    });

    expect(mockApiService.getHealth).toHaveBeenCalledTimes(2);
  });

  it('should set up WebSocket subscription', () => {
    renderHook(() => useHealth());

    expect(mockWebsocketService.subscribe).toHaveBeenCalledWith(expect.any(Function));
  });

  it('should update health data from WebSocket messages', async () => {
    let messageHandler: (message: any) => void;
    mockWebsocketService.subscribe.mockImplementation((handler) => {
      messageHandler = handler;
      return () => {};
    });

    const { result } = renderHook(() => useHealth());

    await waitFor(() => {
      expect(result.current.loading).toBe(false);
    });

    const initialHealth = result.current.health;
    expect(initialHealth?.overall_status).toBe('healthy');

    // Simulate WebSocket message
    const updatedHealth = {
      ...initialHealth,
      overall_status: 'degraded' as const,
    };

    messageHandler!({
      type: 'health_update',
      data: updatedHealth,
      timestamp: '2024-01-01T12:01:00Z',
    });

    await waitFor(() => {
      expect(result.current.health?.overall_status).toBe('degraded');
    });

    expect(result.current.error).toBe(null);
  });
});

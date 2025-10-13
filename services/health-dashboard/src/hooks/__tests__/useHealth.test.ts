import { describe, it, expect, beforeEach, vi } from 'vitest';
import { renderHook, waitFor } from '@testing-library/react';
import { useHealth } from '../useHealth';
import { server } from '../../tests/mocks/server';
import { http, HttpResponse } from 'msw';

describe('useHealth Hook', () => {
  beforeEach(() => {
    vi.useFakeTimers();
  });

  it('should fetch health data successfully', async () => {
    const { result } = renderHook(() => useHealth(1000));
    
    // Initially loading
    expect(result.current.loading).toBe(true);
    expect(result.current.health).toBeNull();
    expect(result.current.error).toBeNull();
    
    // Wait for data to load
    await waitFor(() => {
      expect(result.current.loading).toBe(false);
    });
    
    // Verify health data is populated
    expect(result.current.health).toBeDefined();
    expect(result.current.health?.overall_status).toBe('healthy');
    expect(result.current.health?.ingestion_service?.websocket_connection?.is_connected).toBe(true);
    expect(result.current.error).toBeNull();
  });

  it('should handle API error gracefully', async () => {
    // Mock API to return 500 error
    server.use(
      http.get('/api/health', () => {
        return new HttpResponse(null, { status: 500, statusText: 'Internal Server Error' });
      })
    );
    
    const { result } = renderHook(() => useHealth(1000));
    
    // Wait for error to be set
    await waitFor(() => {
      expect(result.current.loading).toBe(false);
    });
    
    // Verify error state
    expect(result.current.health).toBeNull();
    expect(result.current.error).toBeDefined();
    expect(result.current.error).toContain('500');
  });

  it('should handle network error', async () => {
    // Mock network failure
    server.use(
      http.get('/api/health', () => {
        return HttpResponse.error();
      })
    );
    
    const { result } = renderHook(() => useHealth(1000));
    
    // Wait for error to be set
    await waitFor(() => {
      expect(result.current.loading).toBe(false);
    });
    
    // Verify error state
    expect(result.current.health).toBeNull();
    expect(result.current.error).toBeDefined();
  });

  it('should refresh health data on interval', async () => {
    const { result } = renderHook(() => useHealth(1000));
    
    // Wait for initial fetch
    await waitFor(() => {
      expect(result.current.loading).toBe(false);
    });
    
    const initialHealth = result.current.health;
    expect(initialHealth).toBeDefined();
    
    // Mock a different response for the next fetch
    server.use(
      http.get('/api/health', () => {
        return HttpResponse.json({
          overall_status: 'degraded',
          timestamp: new Date().toISOString(),
          ingestion_service: {
            websocket_connection: { is_connected: false, connection_attempts: 10 },
            event_processing: { status: 'degraded', events_per_minute: 10 },
          },
        });
      })
    );
    
    // Advance timer to trigger refresh
    vi.advanceTimersByTime(1000);
    
    // Wait for refresh to complete
    await waitFor(() => {
      expect(result.current.health?.overall_status).toBe('degraded');
    });
  });
});


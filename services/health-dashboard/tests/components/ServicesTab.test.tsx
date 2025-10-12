import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { ServicesTab } from '../../src/components/ServicesTab';
import type { ServiceStatus } from '../../src/types';

describe('ServicesTab', () => {
  const mockServices: ServiceStatus[] = [
    {
      service: 'websocket-ingestion',
      running: true,
      status: 'running',
      port: 8001,
      uptime: '2h 34m',
      metrics: { requests_per_minute: 20.5, error_rate: 0.1 },
    },
    {
      service: 'enrichment-pipeline',
      running: true,
      status: 'running',
      port: 8002,
      uptime: '2h 33m',
      metrics: { requests_per_minute: 15.2, error_rate: 0.2 },
    },
    {
      service: 'weather-api',
      running: true,
      status: 'running',
      uptime: '2h 35m',
    },
  ];

  beforeEach(() => {
    global.fetch = vi.fn(() =>
      Promise.resolve({
        ok: true,
        json: () => Promise.resolve({ services: mockServices }),
      })
    ) as any;

    vi.useFakeTimers();
  });

  afterEach(() => {
    vi.restoreAllMocks();
    vi.useRealTimers();
  });

  it('renders loading state initially', () => {
    render(<ServicesTab darkMode={false} />);
    expect(screen.getByText('Loading services...')).toBeInTheDocument();
  });

  it('fetches and displays services', async () => {
    render(<ServicesTab darkMode={false} />);

    await waitFor(() => {
      expect(screen.getByText('websocket-ingestion')).toBeInTheDocument();
      expect(screen.getByText('enrichment-pipeline')).toBeInTheDocument();
      expect(screen.getByText('weather-api')).toBeInTheDocument();
    });
  });

  it('displays service count in header', async () => {
    render(<ServicesTab darkMode={false} />);

    await waitFor(() => {
      expect(screen.getByText(/Monitoring 3 system services/)).toBeInTheDocument();
    });
  });

  it('groups services into core and external sections', async () => {
    render(<ServicesTab darkMode={false} />);

    await waitFor(() => {
      expect(screen.getByText(/Core Services/)).toBeInTheDocument();
      expect(screen.getByText(/External Data Services/)).toBeInTheDocument();
    });
  });

  it('displays auto-refresh toggle button', async () => {
    render(<ServicesTab darkMode={false} />);

    await waitFor(() => {
      expect(screen.getByText(/Auto-Refresh ON/)).toBeInTheDocument();
    });
  });

  it('toggles auto-refresh when button clicked', async () => {
    render(<ServicesTab darkMode={false} />);

    await waitFor(() => {
      const autoRefreshButton = screen.getByText(/Auto-Refresh ON/);
      expect(autoRefreshButton).toBeInTheDocument();

      fireEvent.click(autoRefreshButton);
      expect(screen.getByText(/Auto-Refresh OFF/)).toBeInTheDocument();
    });
  });

  it('auto-refreshes services every 5 seconds when enabled', async () => {
    render(<ServicesTab darkMode={false} />);

    await waitFor(() => {
      expect(global.fetch).toHaveBeenCalledTimes(1);
    });

    // Advance time by 5 seconds
    vi.advanceTimersByTime(5000);

    await waitFor(() => {
      expect(global.fetch).toHaveBeenCalledTimes(2);
    });

    // Advance time by another 5 seconds
    vi.advanceTimersByTime(5000);

    await waitFor(() => {
      expect(global.fetch).toHaveBeenCalledTimes(3);
    });
  });

  it('stops auto-refresh when disabled', async () => {
    render(<ServicesTab darkMode={false} />);

    await waitFor(() => {
      expect(global.fetch).toHaveBeenCalledTimes(1);
    });

    // Toggle auto-refresh off
    const autoRefreshButton = screen.getByText(/Auto-Refresh ON/);
    fireEvent.click(autoRefreshButton);

    // Advance time - should not trigger additional fetches
    vi.advanceTimersByTime(10000);

    await waitFor(() => {
      expect(global.fetch).toHaveBeenCalledTimes(1); // Still only 1 call
    });
  });

  it('manually refreshes when Refresh Now button clicked', async () => {
    render(<ServicesTab darkMode={false} />);

    await waitFor(() => {
      expect(global.fetch).toHaveBeenCalledTimes(1);
    });

    const refreshButton = screen.getByText(/Refresh Now/);
    fireEvent.click(refreshButton);

    await waitFor(() => {
      expect(global.fetch).toHaveBeenCalledTimes(2);
    });
  });

  it('displays last update time', async () => {
    render(<ServicesTab darkMode={false} />);

    await waitFor(() => {
      expect(screen.getByText(/Last updated:/)).toBeInTheDocument();
    });
  });

  it('handles API error gracefully', async () => {
    global.fetch = vi.fn(() =>
      Promise.resolve({
        ok: false,
        status: 500,
      })
    ) as any;

    render(<ServicesTab darkMode={false} />);

    await waitFor(() => {
      expect(screen.getByText('Error Loading Services')).toBeInTheDocument();
      expect(screen.getByText(/Failed to load services/)).toBeInTheDocument();
    });
  });

  it('displays retry button on error', async () => {
    global.fetch = vi.fn(() =>
      Promise.resolve({
        ok: false,
        status: 500,
      })
    ) as any;

    render(<ServicesTab darkMode={false} />);

    await waitFor(() => {
      const retryButton = screen.getByText('Retry');
      expect(retryButton).toBeInTheDocument();
    });
  });

  it('retries fetch when retry button clicked', async () => {
    global.fetch = vi.fn(() =>
      Promise.resolve({
        ok: false,
        status: 500,
      })
    ) as any;

    render(<ServicesTab darkMode={false} />);

    await waitFor(() => {
      const retryButton = screen.getByText('Retry');
      fireEvent.click(retryButton);

      expect(global.fetch).toHaveBeenCalledTimes(2);
    });
  });

  it('applies dark mode styles correctly', async () => {
    const { container } = render(<ServicesTab darkMode={true} />);

    await waitFor(() => {
      const cards = container.querySelectorAll('.bg-gray-800');
      expect(cards.length).toBeGreaterThan(0);
    });
  });

  it('applies light mode styles correctly', async () => {
    const { container } = render(<ServicesTab darkMode={false} />);

    await waitFor(() => {
      const cards = container.querySelectorAll('.bg-white');
      expect(cards.length).toBeGreaterThan(0);
    });
  });

  it('displays message when no core services found', async () => {
    global.fetch = vi.fn(() =>
      Promise.resolve({
        ok: true,
        json: () => Promise.resolve({ services: [] }),
      })
    ) as any;

    render(<ServicesTab darkMode={false} />);

    await waitFor(() => {
      expect(screen.getByText('No core services found')).toBeInTheDocument();
      expect(screen.getByText('No external services found')).toBeInTheDocument();
    });
  });
});


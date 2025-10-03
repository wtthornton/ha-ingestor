import React from 'react';
import { render, screen } from '@testing-library/react';
import { HealthCard } from '../../src/components/HealthCard';
import { SystemHealth } from '../../src/types';

const mockHealth: SystemHealth = {
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
};

describe('HealthCard', () => {
  it('renders health information correctly', () => {
    render(<HealthCard health={mockHealth} />);
    
    expect(screen.getByText('System Health')).toBeInTheDocument();
    expect(screen.getByText('HEALTHY')).toBeInTheDocument();
    expect(screen.getByText('WebSocket Connection')).toBeInTheDocument();
    expect(screen.getByText('Connected')).toBeInTheDocument();
    expect(screen.getByText('Event Processing')).toBeInTheDocument();
    expect(screen.getByText('50.0 events/min')).toBeInTheDocument();
  });

  it('shows loading state', () => {
    render(<HealthCard health={mockHealth} loading={true} />);
    
    // Check for loading animation elements
    const loadingElements = document.querySelectorAll('.animate-pulse');
    expect(loadingElements.length).toBeGreaterThan(0);
  });

  it('displays error rate with appropriate color', () => {
    const unhealthyHealth = {
      ...mockHealth,
      ingestion_service: {
        ...mockHealth.ingestion_service,
        event_processing: {
          ...mockHealth.ingestion_service.event_processing,
          error_rate: 0.1, // High error rate
        },
      },
    };

    render(<HealthCard health={unhealthyHealth} />);
    
    expect(screen.getByText('10.00%')).toBeInTheDocument();
  });

  it('shows disconnected status for WebSocket', () => {
    const disconnectedHealth = {
      ...mockHealth,
      ingestion_service: {
        ...mockHealth.ingestion_service,
        websocket_connection: {
          ...mockHealth.ingestion_service.websocket_connection,
          is_connected: false,
        },
      },
    };

    render(<HealthCard health={disconnectedHealth} />);
    
    expect(screen.getByText('Disconnected')).toBeInTheDocument();
  });

  it('displays last updated timestamp', () => {
    render(<HealthCard health={mockHealth} />);
    
    expect(screen.getByText(/Last updated:/)).toBeInTheDocument();
  });
});

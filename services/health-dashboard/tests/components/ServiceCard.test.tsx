import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { ServiceCard } from '../../src/components/ServiceCard';
import type { ServiceStatus } from '../../src/types';

describe('ServiceCard', () => {
  const mockService: ServiceStatus = {
    service: 'websocket-ingestion',
    running: true,
    status: 'running',
    port: 8001,
    uptime: '2h 34m',
    metrics: {
      requests_per_minute: 20.5,
      error_rate: 0.1,
    },
  };

  it('renders service name and icon', () => {
    render(
      <ServiceCard
        service={mockService}
        icon="🏠"
        darkMode={false}
      />
    );

    expect(screen.getByText('websocket-ingestion')).toBeInTheDocument();
    expect(screen.getByText('🏠')).toBeInTheDocument();
  });

  it('displays port number when available', () => {
    render(
      <ServiceCard
        service={mockService}
        icon="🏠"
        darkMode={false}
      />
    );

    expect(screen.getByText(/Port 8001/)).toBeInTheDocument();
  });

  it('displays correct status indicator for running service', () => {
    render(
      <ServiceCard
        service={mockService}
        icon="🏠"
        darkMode={false}
      />
    );

    expect(screen.getByText('🟢')).toBeInTheDocument();
    expect(screen.getByText(/running/i)).toBeInTheDocument();
  });

  it('displays correct status indicator for stopped service', () => {
    const stoppedService = { ...mockService, status: 'stopped' as const, running: false };
    render(
      <ServiceCard
        service={stoppedService}
        icon="🏠"
        darkMode={false}
      />
    );

    expect(screen.getByText('⚪')).toBeInTheDocument();
    expect(screen.getByText(/stopped/i)).toBeInTheDocument();
  });

  it('displays correct status indicator for error service', () => {
    const errorService = { ...mockService, status: 'error' as const, error: 'Connection failed' };
    render(
      <ServiceCard
        service={errorService}
        icon="🏠"
        darkMode={false}
      />
    );

    expect(screen.getByText('🔴')).toBeInTheDocument();
    expect(screen.getByText(/error/i)).toBeInTheDocument();
    expect(screen.getByText('Connection failed')).toBeInTheDocument();
  });

  it('displays uptime when available', () => {
    render(
      <ServiceCard
        service={mockService}
        icon="🏠"
        darkMode={false}
      />
    );

    expect(screen.getByText('Uptime')).toBeInTheDocument();
    expect(screen.getByText('2h 34m')).toBeInTheDocument();
  });

  it('displays requests per minute metric', () => {
    render(
      <ServiceCard
        service={mockService}
        icon="🏠"
        darkMode={false}
      />
    );

    expect(screen.getByText('Requests/min')).toBeInTheDocument();
    expect(screen.getByText('20.5')).toBeInTheDocument();
  });

  it('displays error rate metric with correct color', () => {
    render(
      <ServiceCard
        service={mockService}
        icon="🏠"
        darkMode={false}
      />
    );

    expect(screen.getByText('Error Rate')).toBeInTheDocument();
    expect(screen.getByText('0.10%')).toBeInTheDocument();
  });

  it('shows error rate in red when above threshold', () => {
    const highErrorService = {
      ...mockService,
      metrics: { ...mockService.metrics!, error_rate: 6.5 },
    };
    
    render(
      <ServiceCard
        service={highErrorService}
        icon="🏠"
        darkMode={false}
      />
    );

    const errorRateElement = screen.getByText('6.50%');
    expect(errorRateElement).toHaveClass('text-red-600');
  });

  it('calls onViewDetails when View Details button is clicked', () => {
    const onViewDetails = vi.fn();
    render(
      <ServiceCard
        service={mockService}
        icon="🏠"
        darkMode={false}
        onViewDetails={onViewDetails}
      />
    );

    const viewDetailsButton = screen.getByText(/View Details/);
    fireEvent.click(viewDetailsButton);

    expect(onViewDetails).toHaveBeenCalledTimes(1);
  });

  it('calls onConfigure when Configure button is clicked', () => {
    const onConfigure = vi.fn();
    render(
      <ServiceCard
        service={mockService}
        icon="🏠"
        darkMode={false}
        onConfigure={onConfigure}
      />
    );

    const configureButton = screen.getByText(/Configure/);
    fireEvent.click(configureButton);

    expect(onConfigure).toHaveBeenCalledTimes(1);
  });

  it('applies dark mode styles correctly', () => {
    const { container } = render(
      <ServiceCard
        service={mockService}
        icon="🏠"
        darkMode={true}
      />
    );

    expect(container.firstChild).toHaveClass('bg-gray-800');
  });

  it('applies light mode styles correctly', () => {
    const { container } = render(
      <ServiceCard
        service={mockService}
        icon="🏠"
        darkMode={false}
      />
    );

    expect(container.firstChild).toHaveClass('bg-white');
  });

  it('does not render action buttons when callbacks not provided', () => {
    render(
      <ServiceCard
        service={mockService}
        icon="🏠"
        darkMode={false}
      />
    );

    expect(screen.queryByText(/View Details/)).not.toBeInTheDocument();
    expect(screen.queryByText(/Configure/)).not.toBeInTheDocument();
  });
});


import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { ServiceDetailsModal } from '../../src/components/ServiceDetailsModal';
import type { ServiceStatus } from '../../src/types';

describe('ServiceDetailsModal', () => {
  const mockService: ServiceStatus = {
    service: 'websocket-ingestion',
    running: true,
    status: 'running',
    port: 8001,
    uptime: '2h 34m',
    metrics: {
      requests_per_minute: 20.5,
      error_rate: 0.1,
      cpu_usage: 25.5,
      memory_usage: 256,
    },
  };

  const mockOnClose = vi.fn();

  beforeEach(() => {
    mockOnClose.mockClear();
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  it('renders nothing when isOpen is false', () => {
    const { container } = render(
      <ServiceDetailsModal
        service={mockService}
        icon="🏠"
        isOpen={false}
        onClose={mockOnClose}
        darkMode={false}
      />
    );

    expect(container.firstChild).toBeNull();
  });

  it('renders modal when isOpen is true', async () => {
    render(
      <ServiceDetailsModal
        service={mockService}
        icon="🏠"
        isOpen={true}
        onClose={mockOnClose}
        darkMode={false}
      />
    );

    await waitFor(() => {
      expect(screen.getByText('websocket-ingestion')).toBeInTheDocument();
      expect(screen.getByText('🏠')).toBeInTheDocument();
    });
  });

  it('displays service status badge', async () => {
    render(
      <ServiceDetailsModal
        service={mockService}
        icon="🏠"
        isOpen={true}
        onClose={mockOnClose}
        darkMode={false}
      />
    );

    await waitFor(() => {
      expect(screen.getByText(/RUNNING/)).toBeInTheDocument();
    });
  });

  it('closes modal when close button (X) is clicked', async () => {
    render(
      <ServiceDetailsModal
        service={mockService}
        icon="🏠"
        isOpen={true}
        onClose={mockOnClose}
        darkMode={false}
      />
    );

    await waitFor(() => {
      const closeButton = screen.getByText('×');
      fireEvent.click(closeButton);
      expect(mockOnClose).toHaveBeenCalledTimes(1);
    });
  });

  it('closes modal when backdrop is clicked', async () => {
    const { container } = render(
      <ServiceDetailsModal
        service={mockService}
        icon="🏠"
        isOpen={true}
        onClose={mockOnClose}
        darkMode={false}
      />
    );

    await waitFor(() => {
      // Find the backdrop by its className
      const backdrop = container.querySelector('.fixed.inset-0.bg-black');
      if (backdrop) {
        fireEvent.click(backdrop);
        expect(mockOnClose).toHaveBeenCalledTimes(1);
      }
    });
  });

  it('closes modal when Escape key is pressed', async () => {
    render(
      <ServiceDetailsModal
        service={mockService}
        icon="🏠"
        isOpen={true}
        onClose={mockOnClose}
        darkMode={false}
      />
    );

    await waitFor(() => {
      fireEvent.keyDown(document, { key: 'Escape' });
      expect(mockOnClose).toHaveBeenCalledTimes(1);
    });
  });

  it('does not close modal when modal content is clicked', async () => {
    const { container } = render(
      <ServiceDetailsModal
        service={mockService}
        icon="🏠"
        isOpen={true}
        onClose={mockOnClose}
        darkMode={false}
      />
    );

    await waitFor(() => {
      const modalContent = container.querySelector('.relative.w-full.max-w-6xl');
      if (modalContent) {
        fireEvent.click(modalContent);
        expect(mockOnClose).not.toHaveBeenCalled();
      }
    });
  });

  it('displays all tab options', async () => {
    render(
      <ServiceDetailsModal
        service={mockService}
        icon="🏠"
        isOpen={true}
        onClose={mockOnClose}
        darkMode={false}
      />
    );

    await waitFor(() => {
      expect(screen.getByText('📊 Overview')).toBeInTheDocument();
      expect(screen.getByText('📝 Logs')).toBeInTheDocument();
      expect(screen.getByText('📈 Metrics')).toBeInTheDocument();
      expect(screen.getByText('💚 Health')).toBeInTheDocument();
    });
  });

  it('switches between tabs when clicked', async () => {
    render(
      <ServiceDetailsModal
        service={mockService}
        icon="🏠"
        isOpen={true}
        onClose={mockOnClose}
        darkMode={false}
      />
    );

    await waitFor(() => {
      // Overview tab is default
      expect(screen.getByText('Service Information')).toBeInTheDocument();
    });

    // Click Logs tab
    const logsTab = screen.getByText('📝 Logs');
    fireEvent.click(logsTab);

    await waitFor(() => {
      expect(screen.getByText(/Recent Logs/)).toBeInTheDocument();
    });

    // Click Metrics tab
    const metricsTab = screen.getByText('📈 Metrics');
    fireEvent.click(metricsTab);

    await waitFor(() => {
      expect(screen.getByText('Metrics Charts')).toBeInTheDocument();
    });

    // Click Health tab
    const healthTab = screen.getByText('💚 Health');
    fireEvent.click(healthTab);

    await waitFor(() => {
      expect(screen.getByText(/Health Check Summary/)).toBeInTheDocument();
    });
  });

  it('displays service overview information', async () => {
    render(
      <ServiceDetailsModal
        service={mockService}
        icon="🏠"
        isOpen={true}
        onClose={mockOnClose}
        darkMode={false}
      />
    );

    await waitFor(() => {
      expect(screen.getByText('Service Information')).toBeInTheDocument();
      expect(screen.getByText('Resource Usage')).toBeInTheDocument();
      expect(screen.getByText('2h 34m')).toBeInTheDocument();
    });
  });

  it('displays resource usage bars', async () => {
    render(
      <ServiceDetailsModal
        service={mockService}
        icon="🏠"
        isOpen={true}
        onClose={mockOnClose}
        darkMode={false}
      />
    );

    await waitFor(() => {
      expect(screen.getByText('CPU')).toBeInTheDocument();
      expect(screen.getByText('Memory')).toBeInTheDocument();
    });
  });

  it('displays logs in logs tab', async () => {
    render(
      <ServiceDetailsModal
        service={mockService}
        icon="🏠"
        isOpen={true}
        onClose={mockOnClose}
        darkMode={false}
      />
    );

    // Switch to logs tab
    const logsTab = screen.getByText('📝 Logs');
    fireEvent.click(logsTab);

    await waitFor(() => {
      expect(screen.getByText(/Recent Logs/)).toBeInTheDocument();
      expect(screen.getByText('📋 Copy Logs')).toBeInTheDocument();
      // Check for log level badges
      const logLevels = screen.queryAllByText(/INFO|WARN|ERROR|DEBUG/);
      expect(logLevels.length).toBeGreaterThan(0);
    });
  });

  it('displays chart.js installation note in metrics tab', async () => {
    render(
      <ServiceDetailsModal
        service={mockService}
        icon="🏠"
        isOpen={true}
        onClose={mockOnClose}
        darkMode={false}
      />
    );

    // Switch to metrics tab
    const metricsTab = screen.getByText('📈 Metrics');
    fireEvent.click(metricsTab);

    await waitFor(() => {
      expect(screen.getByText('Metrics Charts')).toBeInTheDocument();
      expect(screen.getByText(/Installation Required/)).toBeInTheDocument();
      expect(screen.getByText(/npm install chart.js react-chartjs-2/)).toBeInTheDocument();
    });
  });

  it('displays health check summary in health tab', async () => {
    render(
      <ServiceDetailsModal
        service={mockService}
        icon="🏠"
        isOpen={true}
        onClose={mockOnClose}
        darkMode={false}
      />
    );

    // Switch to health tab
    const healthTab = screen.getByText('💚 Health');
    fireEvent.click(healthTab);

    await waitFor(() => {
      expect(screen.getByText(/Health Check Summary/)).toBeInTheDocument();
      expect(screen.getByText('Uptime')).toBeInTheDocument();
      expect(screen.getByText('Total Checks')).toBeInTheDocument();
      expect(screen.getByText('Failed')).toBeInTheDocument();
      expect(screen.getByText(/Health Timeline/)).toBeInTheDocument();
    });
  });

  it('applies dark mode styles correctly', async () => {
    const { container } = render(
      <ServiceDetailsModal
        service={mockService}
        icon="🏠"
        isOpen={true}
        onClose={mockOnClose}
        darkMode={true}
      />
    );

    await waitFor(() => {
      const modalContent = container.querySelector('.bg-gray-800.text-white');
      expect(modalContent).toBeInTheDocument();
    });
  });

  it('applies light mode styles correctly', async () => {
    const { container } = render(
      <ServiceDetailsModal
        service={mockService}
        icon="🏠"
        isOpen={true}
        onClose={mockOnClose}
        darkMode={false}
      />
    );

    await waitFor(() => {
      const modalContent = container.querySelector('.bg-white.text-gray-900');
      expect(modalContent).toBeInTheDocument();
    });
  });

  it('displays port mappings when available', async () => {
    render(
      <ServiceDetailsModal
        service={mockService}
        icon="🏠"
        isOpen={true}
        onClose={mockOnClose}
        darkMode={false}
      />
    );

    await waitFor(() => {
      expect(screen.getByText('Port Mappings')).toBeInTheDocument();
    });
  });

  it('prevents body scroll when modal is open', () => {
    render(
      <ServiceDetailsModal
        service={mockService}
        icon="🏠"
        isOpen={true}
        onClose={mockOnClose}
        darkMode={false}
      />
    );

    expect(document.body.style.overflow).toBe('hidden');
  });

  it('restores body scroll when modal is closed', () => {
    const { rerender } = render(
      <ServiceDetailsModal
        service={mockService}
        icon="🏠"
        isOpen={true}
        onClose={mockOnClose}
        darkMode={false}
      />
    );

    expect(document.body.style.overflow).toBe('hidden');

    rerender(
      <ServiceDetailsModal
        service={mockService}
        icon="🏠"
        isOpen={false}
        onClose={mockOnClose}
        darkMode={false}
      />
    );

    expect(document.body.style.overflow).toBe('unset');
  });

  it('displays loading state initially', () => {
    render(
      <ServiceDetailsModal
        service={mockService}
        icon="🏠"
        isOpen={true}
        onClose={mockOnClose}
        darkMode={false}
      />
    );

    // Should show loading spinner initially
    const spinner = document.querySelector('.animate-spin');
    expect(spinner).toBeInTheDocument();
  });
});


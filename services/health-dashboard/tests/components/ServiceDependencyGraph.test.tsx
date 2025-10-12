import { describe, it, expect } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { ServiceDependencyGraph } from '../../src/components/ServiceDependencyGraph';
import type { ServiceStatus } from '../../src/types';

describe('ServiceDependencyGraph', () => {
  const mockServices: ServiceStatus[] = [
    {
      service: 'websocket-ingestion',
      running: true,
      status: 'running',
    },
    {
      service: 'enrichment-pipeline',
      running: true,
      status: 'running',
    },
    {
      service: 'influxdb',
      running: true,
      status: 'running',
    },
    {
      service: 'weather-api',
      running: true,
      status: 'running',
    },
  ];

  it('renders header and description', () => {
    render(<ServiceDependencyGraph services={mockServices} darkMode={false} />);

    expect(screen.getByText(/Service Dependencies & Data Flow/)).toBeInTheDocument();
    expect(screen.getByText(/Click on any service to highlight its dependencies/)).toBeInTheDocument();
  });

  it('renders legend with all status types', () => {
    render(<ServiceDependencyGraph services={mockServices} darkMode={false} />);

    expect(screen.getByText('Running')).toBeInTheDocument();
    expect(screen.getByText('Degraded')).toBeInTheDocument();
    expect(screen.getByText('Error')).toBeInTheDocument();
    expect(screen.getByText('Unknown')).toBeInTheDocument();
  });

  it('renders all service nodes', () => {
    render(<ServiceDependencyGraph services={mockServices} darkMode={false} />);

    // Core services
    expect(screen.getByText('Home Assistant')).toBeInTheDocument();
    expect(screen.getByText(/WebSocket/)).toBeInTheDocument();
    expect(screen.getByText(/Enrichment/)).toBeInTheDocument();
    expect(screen.getByText('InfluxDB')).toBeInTheDocument();

    // External services
    expect(screen.getByText('Weather API')).toBeInTheDocument();
    expect(screen.getByText('Carbon Intensity')).toBeInTheDocument();
    expect(screen.getByText('Electricity Pricing')).toBeInTheDocument();
    expect(screen.getByText('Air Quality')).toBeInTheDocument();
    expect(screen.getByText('Calendar')).toBeInTheDocument();
    expect(screen.getByText('Smart Meter')).toBeInTheDocument();

    // Admin services
    expect(screen.getByText(/Data.*Retention/)).toBeInTheDocument();
    expect(screen.getByText(/Admin.*API/)).toBeInTheDocument();
    expect(screen.getByText(/Health.*Dashboard/)).toBeInTheDocument();
  });

  it('displays service icons', () => {
    render(<ServiceDependencyGraph services={mockServices} darkMode={false} />);

    expect(screen.getByText('🏠')).toBeInTheDocument(); // Home Assistant
    expect(screen.getByText('📡')).toBeInTheDocument(); // WebSocket
    expect(screen.getByText('🔄')).toBeInTheDocument(); // Enrichment
    expect(screen.getByText('🗄️')).toBeInTheDocument(); // InfluxDB
    expect(screen.getByText('☁️')).toBeInTheDocument(); // Weather
  });

  it('highlights selected node when clicked', async () => {
    const { container } = render(<ServiceDependencyGraph services={mockServices} darkMode={false} />);

    // Find and click the WebSocket Ingestion node
    const websocketNode = screen.getByText(/WebSocket/);
    fireEvent.click(websocketNode.closest('div[class*="cursor-pointer"]') as Element);

    await waitFor(() => {
      expect(screen.getByText(/Selected:/)).toBeInTheDocument();
      expect(screen.getByText(/WebSocket.*Ingestion/)).toBeInTheDocument();
    });
  });

  it('shows clear selection button when node is selected', async () => {
    render(<ServiceDependencyGraph services={mockServices} darkMode={false} />);

    // Click a node
    const enrichmentNode = screen.getByText(/Enrichment/);
    fireEvent.click(enrichmentNode.closest('div[class*="cursor-pointer"]') as Element);

    await waitFor(() => {
      const clearButton = screen.getByText('Clear Selection');
      expect(clearButton).toBeInTheDocument();
    });
  });

  it('clears selection when clear button is clicked', async () => {
    render(<ServiceDependencyGraph services={mockServices} darkMode={false} />);

    // Select a node
    const influxNode = screen.getByText('InfluxDB');
    fireEvent.click(influxNode.closest('div[class*="cursor-pointer"]') as Element);

    await waitFor(() => {
      expect(screen.getByText('Clear Selection')).toBeInTheDocument();
    });

    // Click clear button
    const clearButton = screen.getByText('Clear Selection');
    fireEvent.click(clearButton);

    await waitFor(() => {
      expect(screen.queryByText('Clear Selection')).not.toBeInTheDocument();
    });
  });

  it('toggles selection when clicking the same node twice', async () => {
    render(<ServiceDependencyGraph services={mockServices} darkMode={false} />);

    const node = screen.getByText('Weather API');
    const clickableNode = node.closest('div[class*="cursor-pointer"]') as Element;

    // First click - select
    fireEvent.click(clickableNode);
    await waitFor(() => {
      expect(screen.getByText('Clear Selection')).toBeInTheDocument();
    });

    // Second click - deselect
    fireEvent.click(clickableNode);
    await waitFor(() => {
      expect(screen.queryByText('Clear Selection')).not.toBeInTheDocument();
    });
  });

  it('shows tooltip on hover', async () => {
    render(<ServiceDependencyGraph services={mockServices} darkMode={false} />);

    const websocketNode = screen.getByText(/WebSocket/);
    const clickableNode = websocketNode.closest('div[class*="cursor-pointer"]') as Element;

    fireEvent.mouseEnter(clickableNode);

    await waitFor(() => {
      expect(screen.getByText('Captures HA events')).toBeInTheDocument();
    });
  });

  it('hides tooltip on mouse leave', async () => {
    render(<ServiceDependencyGraph services={mockServices} darkMode={false} />);

    const node = screen.getByText(/Enrichment/);
    const clickableNode = node.closest('div[class*="cursor-pointer"]') as Element;

    fireEvent.mouseEnter(clickableNode);
    await waitFor(() => {
      expect(screen.getByText('Combines all data sources')).toBeInTheDocument();
    });

    fireEvent.mouseLeave(clickableNode);
    await waitFor(() => {
      expect(screen.queryByText('Combines all data sources')).not.toBeInTheDocument();
    });
  });

  it('applies correct status colors for running services', () => {
    const { container } = render(<ServiceDependencyGraph services={mockServices} darkMode={false} />);

    // Should have green status for running services
    const runningNodes = container.querySelectorAll('.bg-green-100');
    expect(runningNodes.length).toBeGreaterThan(0);
  });

  it('applies correct status colors for error services', () => {
    const errorServices: ServiceStatus[] = [
      {
        service: 'websocket-ingestion',
        running: false,
        status: 'error',
      },
    ];

    const { container } = render(<ServiceDependencyGraph services={errorServices} darkMode={false} />);

    // Should have red status for error services
    const errorNodes = container.querySelectorAll('.bg-red-100');
    expect(errorNodes.length).toBeGreaterThan(0);
  });

  it('applies dark mode styles correctly', () => {
    const { container } = render(<ServiceDependencyGraph services={mockServices} darkMode={true} />);

    // Should have dark background colors
    const darkBgs = container.querySelectorAll('.bg-gray-800');
    expect(darkBgs.length).toBeGreaterThan(0);
  });

  it('applies light mode styles correctly', () => {
    const { container } = render(<ServiceDependencyGraph services={mockServices} darkMode={false} />);

    // Should have white background colors
    const lightBgs = container.querySelectorAll('.bg-white');
    expect(lightBgs.length).toBeGreaterThan(0);
  });

  it('renders all dependency arrows', () => {
    render(<ServiceDependencyGraph services={mockServices} darkMode={false} />);

    // Check for arrow symbols
    const arrows = screen.getAllByText(/↓/);
    expect(arrows.length).toBeGreaterThan(0);
  });

  it('renders external data sources section', () => {
    render(<ServiceDependencyGraph services={mockServices} darkMode={false} />);

    expect(screen.getByText('External Data Sources')).toBeInTheDocument();
  });

  it('displays correct node for unknown service status', () => {
    const unknownServices: ServiceStatus[] = [
      {
        service: 'unknown-service',
        running: true,
        status: 'running',
      },
    ];

    const { container } = render(<ServiceDependencyGraph services={unknownServices} darkMode={false} />);

    // Should have gray status for unknown services
    const unknownNodes = container.querySelectorAll('.bg-gray-100');
    expect(unknownNodes.length).toBeGreaterThan(0);
  });

  it('renders responsive layout classes', () => {
    const { container } = render(<ServiceDependencyGraph services={mockServices} darkMode={false} />);

    // Check for responsive grid classes
    const gridContainers = container.querySelectorAll('.grid-cols-2');
    expect(gridContainers.length).toBeGreaterThan(0);
  });

  it('renders overflow handling for long content', () => {
    const { container } = render(<ServiceDependencyGraph services={mockServices} darkMode={false} />);

    // Check for overflow-x-auto
    const scrollableContainer = container.querySelector('.overflow-x-auto');
    expect(scrollableContainer).toBeInTheDocument();
  });

  it('displays all layers of service architecture', () => {
    render(<ServiceDependencyGraph services={mockServices} darkMode={false} />);

    // Layer 1: Source
    expect(screen.getByText('Home Assistant')).toBeInTheDocument();

    // Layer 2: Ingestion
    expect(screen.getByText(/WebSocket/)).toBeInTheDocument();

    // Layer 3: External (checked above)
    expect(screen.getByText('Weather API')).toBeInTheDocument();

    // Layer 4: Processing
    expect(screen.getByText(/Enrichment/)).toBeInTheDocument();

    // Layer 5: Storage
    expect(screen.getByText('InfluxDB')).toBeInTheDocument();
  });

  it('shows "you are here" tooltip for health dashboard', async () => {
    render(<ServiceDependencyGraph services={mockServices} darkMode={false} />);

    const dashboardNode = screen.getByText(/Health.*Dashboard/);
    const clickableNode = dashboardNode.closest('div[class*="cursor-pointer"]') as Element;

    fireEvent.mouseEnter(clickableNode);

    await waitFor(() => {
      expect(screen.getByText(/you are here/i)).toBeInTheDocument();
    });
  });
});


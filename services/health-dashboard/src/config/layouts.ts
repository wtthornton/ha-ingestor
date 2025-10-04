import { LayoutConfig } from '../types';

export const LAYOUT_CONFIGS: Record<string, LayoutConfig> = {
  overview: {
    id: 'overview',
    name: 'Overview',
    description: 'High-level system status with key metrics',
    grid: {
      columns: 12,
      rows: 8,
      gap: 16,
    },
    widgets: [
      {
        id: 'health-card',
        type: 'HealthCard',
        position: { x: 0, y: 0, w: 4, h: 2 },
        props: {},
      },
      {
        id: 'event-rate-chart',
        type: 'MetricsChart',
        position: { x: 4, y: 0, w: 8, h: 2 },
        props: {
          title: 'Event Rate (24h)',
          type: 'line',
        },
      },
      {
        id: 'event-feed',
        type: 'EventFeed',
        position: { x: 0, y: 2, w: 12, h: 6 },
        props: {
          limit: 20,
        },
      },
    ],
  },
  detailed: {
    id: 'detailed',
    name: 'Detailed',
    description: 'Comprehensive monitoring with all available data',
    grid: {
      columns: 12,
      rows: 10,
      gap: 16,
    },
    widgets: [
      {
        id: 'health-card',
        type: 'HealthCard',
        position: { x: 0, y: 0, w: 6, h: 3 },
        props: {},
      },
      {
        id: 'event-rate-chart',
        type: 'MetricsChart',
        position: { x: 6, y: 0, w: 6, h: 3 },
        props: {
          title: 'Event Rate (24h)',
          type: 'line',
        },
      },
      {
        id: 'error-rate-chart',
        type: 'MetricsChart',
        position: { x: 0, y: 3, w: 6, h: 3 },
        props: {
          title: 'Error Rate (24h)',
          type: 'bar',
        },
      },
      {
        id: 'service-status-chart',
        type: 'MetricsChart',
        position: { x: 6, y: 3, w: 6, h: 3 },
        props: {
          title: 'Service Status Distribution',
          type: 'doughnut',
        },
      },
      {
        id: 'event-feed',
        type: 'EventFeed',
        position: { x: 0, y: 6, w: 12, h: 4 },
        props: {
          limit: 50,
        },
      },
    ],
  },
  mobile: {
    id: 'mobile',
    name: 'Mobile',
    description: 'Touch-optimized layout for mobile devices',
    grid: {
      columns: 1,
      rows: 12,
      gap: 12,
    },
    widgets: [
      {
        id: 'health-card',
        type: 'HealthCard',
        position: { x: 0, y: 0, w: 1, h: 3 },
        props: {},
      },
      {
        id: 'event-rate-chart',
        type: 'MetricsChart',
        position: { x: 0, y: 3, w: 1, h: 3 },
        props: {
          title: 'Event Rate (24h)',
          type: 'line',
        },
      },
      {
        id: 'event-feed',
        type: 'EventFeed',
        position: { x: 0, y: 6, w: 1, h: 6 },
        props: {
          limit: 15,
        },
      },
    ],
  },
  compact: {
    id: 'compact',
    name: 'Compact',
    description: 'Space-efficient layout for smaller screens',
    grid: {
      columns: 6,
      rows: 6,
      gap: 12,
    },
    widgets: [
      {
        id: 'health-card',
        type: 'HealthCard',
        position: { x: 0, y: 0, w: 3, h: 2 },
        props: {},
      },
      {
        id: 'event-rate-chart',
        type: 'MetricsChart',
        position: { x: 3, y: 0, w: 3, h: 2 },
        props: {
          title: 'Event Rate (24h)',
          type: 'line',
        },
      },
      {
        id: 'event-feed',
        type: 'EventFeed',
        position: { x: 0, y: 2, w: 6, h: 4 },
        props: {
          limit: 25,
        },
      },
    ],
  },
};

export const DEFAULT_LAYOUT = 'overview';

export const getLayoutConfig = (layoutId: string): LayoutConfig | null => {
  return LAYOUT_CONFIGS[layoutId] || null;
};

export const getAllLayouts = (): LayoutConfig[] => {
  return Object.values(LAYOUT_CONFIGS);
};

/**
 * Dashboard Types
 * 
 * Type definitions for dashboard customization and widgets
 * Epic 15.3: Dashboard Customization & Layout
 */

export interface Widget {
  id: string;
  type: 'health' | 'metrics' | 'services' | 'alerts' | 'events' | 'chart' | 'custom';
  title: string;
  config?: any;
}

export interface LayoutItem {
  i: string;  // Widget ID
  x: number;  // X position in grid
  y: number;  // Y position in grid
  w: number;  // Width in grid units
  h: number;  // Height in grid units
  minW?: number;
  maxW?: number;
  minH?: number;
  maxH?: number;
  static?: boolean;  // Cannot be moved/resized
}

export interface DashboardLayout {
  name: string;
  description: string;
  widgets: Widget[];
  layout: {
    lg: LayoutItem[];
    md: LayoutItem[];
    sm: LayoutItem[];
    xs: LayoutItem[];
  };
}

export type LayoutPreset = 'default' | 'operations' | 'development' | 'executive';

export const DEFAULT_LAYOUTS: Record<LayoutPreset, DashboardLayout> = {
  default: {
    name: 'Default',
    description: 'Balanced view for general monitoring',
    widgets: [
      { id: 'health-1', type: 'health', title: 'System Health' },
      { id: 'metrics-1', type: 'metrics', title: 'Key Metrics' },
      { id: 'services-1', type: 'services', title: 'Services' },
      { id: 'alerts-1', type: 'alerts', title: 'Recent Alerts' }
    ],
    layout: {
      lg: [
        { i: 'health-1', x: 0, y: 0, w: 6, h: 2 },
        { i: 'metrics-1', x: 6, y: 0, w: 6, h: 2 },
        { i: 'services-1', x: 0, y: 2, w: 8, h: 3 },
        { i: 'alerts-1', x: 8, y: 2, w: 4, h: 3 }
      ],
      md: [
        { i: 'health-1', x: 0, y: 0, w: 5, h: 2 },
        { i: 'metrics-1', x: 5, y: 0, w: 5, h: 2 },
        { i: 'services-1', x: 0, y: 2, w: 10, h: 3 },
        { i: 'alerts-1', x: 0, y: 5, w: 10, h: 2 }
      ],
      sm: [
        { i: 'health-1', x: 0, y: 0, w: 6, h: 2 },
        { i: 'metrics-1', x: 0, y: 2, w: 6, h: 2 },
        { i: 'services-1', x: 0, y: 4, w: 6, h: 3 },
        { i: 'alerts-1', x: 0, y: 7, w: 6, h: 2 }
      ],
      xs: [
        { i: 'health-1', x: 0, y: 0, w: 4, h: 2 },
        { i: 'metrics-1', x: 0, y: 2, w: 4, h: 2 },
        { i: 'services-1', x: 0, y: 4, w: 4, h: 3 },
        { i: 'alerts-1', x: 0, y: 7, w: 4, h: 2 }
      ]
    }
  },
  operations: {
    name: 'Operations',
    description: 'Focus on service health and alerts',
    widgets: [
      { id: 'services-1', type: 'services', title: 'Services' },
      { id: 'alerts-1', type: 'alerts', title: 'Critical Alerts' },
      { id: 'events-1', type: 'events', title: 'Live Events' },
      { id: 'health-1', type: 'health', title: 'System Health' }
    ],
    layout: {
      lg: [
        { i: 'services-1', x: 0, y: 0, w: 8, h: 4 },
        { i: 'alerts-1', x: 8, y: 0, w: 4, h: 2 },
        { i: 'events-1', x: 8, y: 2, w: 4, h: 2 },
        { i: 'health-1', x: 0, y: 4, w: 12, h: 2 }
      ],
      md: [
        { i: 'services-1', x: 0, y: 0, w: 10, h: 3 },
        { i: 'alerts-1', x: 0, y: 3, w: 10, h: 2 },
        { i: 'events-1', x: 0, y: 5, w: 10, h: 2 },
        { i: 'health-1', x: 0, y: 7, w: 10, h: 2 }
      ],
      sm: [
        { i: 'services-1', x: 0, y: 0, w: 6, h: 3 },
        { i: 'alerts-1', x: 0, y: 3, w: 6, h: 2 },
        { i: 'events-1', x: 0, y: 5, w: 6, h: 2 },
        { i: 'health-1', x: 0, y: 7, w: 6, h: 2 }
      ],
      xs: [
        { i: 'services-1', x: 0, y: 0, w: 4, h: 3 },
        { i: 'alerts-1', x: 0, y: 3, w: 4, h: 2 },
        { i: 'events-1', x: 0, y: 5, w: 4, h: 2 },
        { i: 'health-1', x: 0, y: 7, w: 4, h: 2 }
      ]
    }
  },
  development: {
    name: 'Development',
    description: 'Focus on events and logs for debugging',
    widgets: [
      { id: 'events-1', type: 'events', title: 'Live Events' },
      { id: 'metrics-1', type: 'metrics', title: 'Performance Metrics' },
      { id: 'services-1', type: 'services', title: 'Services' }
    ],
    layout: {
      lg: [
        { i: 'events-1', x: 0, y: 0, w: 8, h: 4 },
        { i: 'metrics-1', x: 8, y: 0, w: 4, h: 4 },
        { i: 'services-1', x: 0, y: 4, w: 12, h: 3 }
      ],
      md: [
        { i: 'events-1', x: 0, y: 0, w: 10, h: 4 },
        { i: 'metrics-1', x: 0, y: 4, w: 10, h: 3 },
        { i: 'services-1', x: 0, y: 7, w: 10, h: 3 }
      ],
      sm: [
        { i: 'events-1', x: 0, y: 0, w: 6, h: 4 },
        { i: 'metrics-1', x: 0, y: 4, w: 6, h: 3 },
        { i: 'services-1', x: 0, y: 7, w: 6, h: 3 }
      ],
      xs: [
        { i: 'events-1', x: 0, y: 0, w: 4, h: 4 },
        { i: 'metrics-1', x: 0, y: 4, w: 4, h: 3 },
        { i: 'services-1', x: 0, y: 7, w: 4, h: 3 }
      ]
    }
  },
  executive: {
    name: 'Executive',
    description: 'High-level overview with key metrics',
    widgets: [
      { id: 'metrics-1', type: 'metrics', title: 'Key Metrics' },
      { id: 'chart-1', type: 'chart', title: 'Trends' },
      { id: 'health-1', type: 'health', title: 'System Health' }
    ],
    layout: {
      lg: [
        { i: 'metrics-1', x: 0, y: 0, w: 12, h: 2 },
        { i: 'chart-1', x: 0, y: 2, w: 8, h: 3 },
        { i: 'health-1', x: 8, y: 2, w: 4, h: 3 }
      ],
      md: [
        { i: 'metrics-1', x: 0, y: 0, w: 10, h: 2 },
        { i: 'chart-1', x: 0, y: 2, w: 10, h: 3 },
        { i: 'health-1', x: 0, y: 5, w: 10, h: 2 }
      ],
      sm: [
        { i: 'metrics-1', x: 0, y: 0, w: 6, h: 2 },
        { i: 'chart-1', x: 0, y: 2, w: 6, h: 3 },
        { i: 'health-1', x: 0, y: 5, w: 6, h: 2 }
      ],
      xs: [
        { i: 'metrics-1', x: 0, y: 0, w: 4, h: 2 },
        { i: 'chart-1', x: 0, y: 2, w: 4, h: 3 },
        { i: 'health-1', x: 0, y: 5, w: 4, h: 2 }
      ]
    }
  }
};


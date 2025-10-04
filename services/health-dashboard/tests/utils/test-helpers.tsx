import React from 'react';
import { render, RenderOptions } from '@testing-library/react';
import { ThemeProvider } from '../../src/contexts/ThemeContext';
import { NotificationProvider } from '../../src/contexts/NotificationContext';
import { LayoutProvider } from '../../src/contexts/LayoutContext';

// Mock WebSocket service
const mockWebSocketService = {
  connect: vi.fn().mockResolvedValue(undefined),
  disconnect: vi.fn(),
  subscribe: vi.fn().mockReturnValue(() => {}),
  onDisconnect: vi.fn().mockReturnValue(() => {}),
  send: vi.fn(),
  isConnected: true,
};

// Mock API service
const mockApiService = {
  getHealth: vi.fn().mockResolvedValue({
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
  }),
  getStatistics: vi.fn().mockResolvedValue({
    total_events: 1000,
    active_entities: 50,
    events_per_minute: 45,
    average_latency: 12,
    uptime: 99.9,
    memory_usage: 75,
    cpu_usage: 45,
  }),
  getEvents: vi.fn().mockResolvedValue([
    {
      id: '1',
      timestamp: '2024-01-01T12:00:00Z',
      entity_id: 'sensor.temperature',
      event_type: 'state_changed',
      new_state: { state: '22.5' },
      attributes: { unit_of_measurement: '°C' },
      domain: 'sensor',
      service: null,
      context: { id: '123' },
    },
    {
      id: '2',
      timestamp: '2024-01-01T12:01:00Z',
      entity_id: 'light.living_room',
      event_type: 'state_changed',
      new_state: { state: 'on' },
      attributes: { brightness: 255 },
      domain: 'light',
      service: null,
      context: { id: '124' },
    },
  ]),
};

// Mock notification service
const mockNotificationService = {
  send: vi.fn(),
  subscribe: vi.fn().mockReturnValue(() => {}),
  updatePreferences: vi.fn(),
  integrateWithWebSocket: vi.fn(),
  integrateWithPerformanceMonitor: vi.fn(),
  integrateWithMaintenance: vi.fn(),
};

// All providers wrapper
const AllTheProviders: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  return (
    <ThemeProvider>
      <NotificationProvider>
        <LayoutProvider>
          {children}
        </LayoutProvider>
      </NotificationProvider>
    </ThemeProvider>
  );
};

// Custom render function with providers
const customRender = (
  ui: React.ReactElement,
  options?: Omit<RenderOptions, 'wrapper'>
) => {
  return render(ui, { wrapper: AllTheProviders, ...options });
};

// Mock services
const mockServices = () => {
  vi.mock('../../src/services/websocket', () => ({
    websocketService: mockWebSocketService,
  }));

  vi.mock('../../src/services/api', () => ({
    apiService: mockApiService,
  }));

  vi.mock('../../src/services/notificationService', () => ({
    notificationService: mockNotificationService,
  }));
};

// Test data factories
export const createMockHealthData = (overrides = {}) => ({
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
  ...overrides,
});

export const createMockStatisticsData = (overrides = {}) => ({
  total_events: 1000,
  active_entities: 50,
  events_per_minute: 45,
  average_latency: 12,
  uptime: 99.9,
  memory_usage: 75,
  cpu_usage: 45,
  ...overrides,
});

export const createMockEventData = (overrides = {}) => ({
  id: '1',
  timestamp: '2024-01-01T12:00:00Z',
  entity_id: 'sensor.temperature',
  event_type: 'state_changed',
  new_state: { state: '22.5' },
  attributes: { unit_of_measurement: '°C' },
  domain: 'sensor',
  service: null,
  context: { id: '123' },
  ...overrides,
});

export const createMockNotification = (overrides = {}) => ({
  id: '1',
  type: 'info',
  title: 'Test Notification',
  message: 'This is a test notification',
  timestamp: new Date(),
  read: false,
  actions: [],
  ...overrides,
});

// Utility functions
export const waitForLoadingToFinish = () => {
  return new Promise(resolve => setTimeout(resolve, 0));
};

export const mockLocalStorage = () => {
  const store: { [key: string]: string } = {};
  
  return {
    getItem: vi.fn((key: string) => store[key] || null),
    setItem: vi.fn((key: string, value: string) => {
      store[key] = value;
    }),
    removeItem: vi.fn((key: string) => {
      delete store[key];
    }),
    clear: vi.fn(() => {
      Object.keys(store).forEach(key => delete store[key]);
    }),
  };
};

export const mockSessionStorage = () => {
  const store: { [key: string]: string } = {};
  
  return {
    getItem: vi.fn((key: string) => store[key] || null),
    setItem: vi.fn((key: string, value: string) => {
      store[key] = value;
    }),
    removeItem: vi.fn((key: string) => {
      delete store[key];
    }),
    clear: vi.fn(() => {
      Object.keys(store).forEach(key => delete store[key]);
    }),
  };
};

export const mockWebSocket = () => {
  const mockWS = {
    send: vi.fn(),
    close: vi.fn(),
    addEventListener: vi.fn(),
    removeEventListener: vi.fn(),
    dispatchEvent: vi.fn(),
    readyState: WebSocket.OPEN,
    url: 'ws://localhost:3000',
    protocol: '',
    extensions: '',
    bufferedAmount: 0,
    binaryType: 'blob' as BinaryType,
    onopen: null,
    onclose: null,
    onmessage: null,
    onerror: null,
  };
  
  vi.stubGlobal('WebSocket', vi.fn(() => mockWS));
  return mockWS;
};

export const mockFetch = (response: any, status = 200) => {
  const mockResponse = {
    ok: status >= 200 && status < 300,
    status,
    json: vi.fn().mockResolvedValue(response),
    text: vi.fn().mockResolvedValue(JSON.stringify(response)),
    blob: vi.fn().mockResolvedValue(new Blob()),
    arrayBuffer: vi.fn().mockResolvedValue(new ArrayBuffer(0)),
    formData: vi.fn().mockResolvedValue(new FormData()),
    clone: vi.fn().mockReturnValue(mockResponse),
    headers: new Headers(),
    redirected: false,
    statusText: 'OK',
    type: 'basic' as ResponseType,
    url: 'http://localhost:3000/api/test',
    body: null,
    bodyUsed: false,
  };
  
  vi.stubGlobal('fetch', vi.fn().mockResolvedValue(mockResponse));
  return mockResponse;
};

// Export everything
export * from '@testing-library/react';
export { customRender as render };
export { mockServices, mockWebSocketService, mockApiService, mockNotificationService };

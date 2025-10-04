// System Health Types
export interface SystemHealth {
  overall_status: 'healthy' | 'degraded' | 'unhealthy';
  admin_api_status: string;
  ingestion_service: IngestionServiceHealth;
  timestamp: string;
}

export interface IngestionServiceHealth {
  status: 'healthy' | 'degraded' | 'unhealthy';
  websocket_connection: WebSocketConnection;
  event_processing: EventProcessing;
  weather_enrichment: WeatherEnrichment;
  influxdb_storage: InfluxDBStorage;
  timestamp: string;
}

export interface WebSocketConnection {
  is_connected: boolean;
  last_connection_time: string;
  connection_attempts: number;
  last_error: string | null;
}

export interface EventProcessing {
  total_events: number;
  events_per_minute: number;
  error_rate: number;
}

export interface WeatherEnrichment {
  enabled: boolean;
  cache_hits: number;
  api_calls: number;
  last_error: string | null;
}

export interface InfluxDBStorage {
  is_connected: boolean;
  last_write_time: string;
  write_errors: number;
}

// Statistics Types
export interface Statistics {
  timestamp: string;
  period: string;
  metrics: Record<string, any>;
  trends: Record<string, any>;
  alerts: Alert[];
}

export interface Alert {
  service: string;
  level: 'critical' | 'error' | 'warning' | 'info';
  message: string;
  timestamp: string;
}

// Event Types
export interface EventData {
  id: string;
  timestamp: string;
  entity_id: string;
  event_type: string;
  old_state?: Record<string, any>;
  new_state?: Record<string, any>;
  attributes: Record<string, any>;
  tags: Record<string, string>;
}

export interface EventFilter {
  entity_id?: string;
  event_type?: string;
  start_time?: string;
  end_time?: string;
  limit?: number;
  offset?: number;
}

// Configuration Types
export interface Configuration {
  [key: string]: any;
}

export interface ConfigUpdate {
  key: string;
  value: any;
  reason?: string;
}

// Dashboard State Types
export interface DashboardState {
  health: SystemHealth | null;
  statistics: Statistics | null;
  events: EventData[];
  configuration: Configuration | null;
  loading: boolean;
  error: string | null;
  lastUpdate: string | null;
}

// Component Props Types
export interface HealthCardProps {
  health: SystemHealth;
  loading?: boolean;
}

export interface MetricsChartProps {
  data: any[];
  type: 'line' | 'bar' | 'doughnut';
  title: string;
  loading?: boolean;
}

export interface EventFeedProps {
  events: EventData[];
  loading?: boolean;
  onFilter?: (filter: EventFilter) => void;
}

export interface ServiceStatusProps {
  service: string;
  status: 'healthy' | 'degraded' | 'unhealthy';
  details: Record<string, any>;
}

// API Response Types
export interface ApiResponse<T> {
  success: boolean;
  data?: T;
  message?: string;
  timestamp: string;
  request_id?: string;
}

export interface ErrorResponse {
  success: false;
  error: string;
  error_code?: string;
  timestamp: string;
  request_id?: string;
}

// WebSocket Types
export interface WebSocketMessage {
  type: 'health_update' | 'stats_update' | 'event_update' | 'config_update';
  data: any;
  timestamp: string;
}

// Chart Data Types
export interface ChartData {
  labels: string[];
  datasets: ChartDataset[];
}

export interface ChartDataset {
  label: string;
  data: number[];
  backgroundColor?: string | string[];
  borderColor?: string | string[];
  borderWidth?: number;
  fill?: boolean;
}

// Layout System Types
export interface LayoutConfig {
  id: string;
  name: string;
  description: string;
  grid: {
    columns: number;
    rows: number;
    gap: number;
  };
  widgets: WidgetConfig[];
}

export interface WidgetConfig {
  id: string;
  type: string;
  position: { x: number; y: number; w: number; h: number };
  props: Record<string, any>;
}

export interface LayoutState {
  currentLayout: string;
  availableLayouts: LayoutConfig[];
  isTransitioning: boolean;
}

export type LayoutType = 'overview' | 'detailed' | 'mobile' | 'compact';

// Utility Types
export type ServiceStatus = 'healthy' | 'degraded' | 'unhealthy';
export type AlertLevel = 'critical' | 'error' | 'warning' | 'info';
export type ChartType = 'line' | 'bar' | 'doughnut' | 'pie';
export type RefreshInterval = 1000 | 5000 | 10000 | 30000 | 60000; // milliseconds

// Notification Types
export * from './notification';

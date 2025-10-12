export interface HealthStatus {
  status: 'healthy' | 'degraded' | 'unhealthy';
  services: {
    [key: string]: {
      status: 'healthy' | 'degraded' | 'unhealthy';
      response_time?: number;
      last_error?: string;
    };
  };
  metrics: {
    websocket_connection: {
      status: 'connected' | 'disconnected';
      last_message_time: string;
      connection_uptime: number;
    };
    event_processing: {
      status: 'healthy' | 'degraded' | 'unhealthy';
      events_per_minute: number;
      last_event_time: string;
      processing_lag: number;
    };
    weather_enrichment: {
      enabled: boolean;
      cache_hits: number;
      api_calls: number;
      last_error?: string;
    };
    influxdb_storage: {
      is_connected: boolean;
      last_write_time: string;
      write_errors: number;
    };
  };
  timestamp: string;
}

export interface DataSourceHealth {
  status: 'healthy' | 'degraded';
  service: string;
  uptime_seconds: number;
  last_successful_fetch: string | null;
  total_fetches: number;
  failed_fetches: number;
  success_rate: number;
  timestamp: string;
  oauth_valid?: boolean;
}

export interface DataSourceMetrics {
  carbon_intensity?: {
    current: number;
    renewable_pct: number;
    forecast_1h: number;
  };
  electricity_pricing?: {
    current_price: number;
    currency: string;
    cheapest_hours: number[];
  };
  air_quality?: {
    aqi: number;
    category: string;
  };
  occupancy?: {
    currently_home: boolean;
    wfh_today: boolean;
    confidence: number;
  };
  smart_meter?: {
    total_power_w: number;
    daily_kwh: number;
  };
}

export interface Statistics {
  timestamp: string;
  period: string;
  metrics: {
    total_events: number;
    events_per_minute: number;
    processing_time_avg: number;
    error_rate: number;
  };
  trends: {
    [key: string]: any;
  };
  alerts: Array<{
    type: string;
    message: string;
    severity: 'info' | 'warning' | 'error';
  }>;
}

// Service Management Types (Phase 1, 2, 3)
export interface ServiceStatus {
  service: string;
  running: boolean;
  status: 'running' | 'stopped' | 'error' | 'degraded';
  timestamp?: string;
  error?: string;
  port?: number;
  uptime?: string;
  metrics?: ServiceMetrics;
}

export interface ServiceMetrics {
  requests_per_minute?: number;
  error_rate?: number;
  cpu_usage?: number;
  memory_usage?: number;
  total_requests?: number;
}

export interface ServiceGroup {
  title: string;
  description: string;
  services: ServiceStatus[];
}

export type ServiceType = 'core' | 'external' | 'storage' | 'ui';

export interface ServiceDefinition {
  id: string;
  name: string;
  icon: string;
  type: ServiceType;
  port?: number;
  description: string;
}

export interface ServiceDetails {
  service: string;
  status: 'running' | 'stopped' | 'error' | 'degraded';
  uptime: string;
  container_id?: string;
  image?: string;
  last_restart?: string;
  port_mappings?: string[];
  environment?: Record<string, string>;
}

export interface ServiceLog {
  timestamp: string;
  level: 'INFO' | 'WARN' | 'ERROR' | 'DEBUG';
  message: string;
}

export interface ServiceMetricPoint {
  timestamp: string;
  requests: number;
  errors: number;
  response_time?: number;
}

export interface ServiceHealthCheck {
  timestamp: string;
  status: 'healthy' | 'unhealthy';
  response_time?: number;
  error?: string;
}

export interface ServiceResourceUsage {
  cpu_percent: number;
  memory_used_mb: number;
  memory_limit_mb: number;
  memory_percent: number;
}

export interface ServiceDependency {
  from: string;
  to: string;
  type: 'data_flow' | 'api_call' | 'storage';
  description?: string;
}

export interface ServiceNode {
  id: string;
  name: string;
  icon: string;
  type: ServiceType;
  layer: number;
  position: number;
}
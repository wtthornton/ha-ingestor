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

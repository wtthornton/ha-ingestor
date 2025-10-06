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

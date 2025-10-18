/**
 * Health monitoring types for HA Setup Service
 * 
 * Context7 Pattern: TypeScript types matching backend Pydantic schemas
 */

export enum HealthStatus {
  HEALTHY = 'healthy',
  WARNING = 'warning',
  CRITICAL = 'critical',
  UNKNOWN = 'unknown'
}

export enum IntegrationStatus {
  HEALTHY = 'healthy',
  WARNING = 'warning',
  ERROR = 'error',
  NOT_CONFIGURED = 'not_configured'
}

export interface PerformanceMetrics {
  response_time_ms: number;
  cpu_usage_percent?: number;
  memory_usage_mb?: number;
  uptime_seconds?: number;
}

export interface IntegrationHealthDetail {
  name: string;
  type: string;
  status: IntegrationStatus;
  is_configured: boolean;
  is_connected: boolean;
  error_message?: string;
  last_check?: string;
  check_details?: Record<string, any>;
}

export interface EnvironmentHealth {
  health_score: number;
  ha_status: HealthStatus;
  ha_version?: string;
  integrations: IntegrationHealthDetail[];
  performance: PerformanceMetrics;
  issues_detected: string[];
  timestamp: string;
}

export interface IntegrationHealthResponse {
  timestamp: string;
  total_integrations: number;
  healthy_count: number;
  warning_count: number;
  error_count: number;
  not_configured_count: number;
  integrations: IntegrationHealthDetail[];
}

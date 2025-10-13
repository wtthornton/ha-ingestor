/**
 * Enhanced Health Monitoring Types
 * Epic 17.2: Enhanced Service Health Monitoring
 */

export enum HealthStatus {
  HEALTHY = 'healthy',
  WARNING = 'warning',
  CRITICAL = 'critical',
  UNKNOWN = 'unknown'
}

export enum DependencyType {
  DATABASE = 'database',
  CACHE = 'cache',
  API = 'api',
  WEBSOCKET = 'websocket',
  MESSAGE_QUEUE = 'message_queue',
  FILE_SYSTEM = 'file_system',
  EXTERNAL_SERVICE = 'external_service'
}

export interface DependencyHealth {
  name: string;
  type: DependencyType;
  status: HealthStatus;
  response_time_ms?: number;
  message?: string;
  details?: Record<string, any>;
}

export interface ServiceHealthMetrics {
  uptime_seconds?: number;
  uptime_human?: string;
  start_time?: string;
  current_time?: string;
  memory_usage?: Record<string, any>;
  cpu_usage?: Record<string, any>;
  [key: string]: any;
}

export interface ServiceHealthResponse {
  service: string;
  status: HealthStatus;
  timestamp: string;
  uptime_seconds?: number;
  version?: string;
  dependencies?: DependencyHealth[];
  metrics?: ServiceHealthMetrics;
  message?: string;
}

/**
 * Get status color for UI display
 */
export function getStatusColor(status: HealthStatus, darkMode: boolean = false): string {
  const colors = {
    [HealthStatus.HEALTHY]: darkMode ? 'text-green-400 bg-green-900/30' : 'text-green-700 bg-green-50',
    [HealthStatus.WARNING]: darkMode ? 'text-yellow-400 bg-yellow-900/30' : 'text-yellow-700 bg-yellow-50',
    [HealthStatus.CRITICAL]: darkMode ? 'text-red-400 bg-red-900/30' : 'text-red-700 bg-red-50',
    [HealthStatus.UNKNOWN]: darkMode ? 'text-gray-400 bg-gray-800/30' : 'text-gray-600 bg-gray-100'
  };
  
  return colors[status] || colors[HealthStatus.UNKNOWN];
}

/**
 * Get status icon emoji
 */
export function getStatusIcon(status: HealthStatus): string {
  const icons = {
    [HealthStatus.HEALTHY]: '✅',
    [HealthStatus.WARNING]: '⚠️',
    [HealthStatus.CRITICAL]: '❌',
    [HealthStatus.UNKNOWN]: '❓'
  };
  
  return icons[status] || icons[HealthStatus.UNKNOWN];
}

/**
 * Get dependency type icon
 */
export function getDependencyTypeIcon(type: DependencyType): string {
  const icons = {
    [DependencyType.DATABASE]: '🗄️',
    [DependencyType.CACHE]: '💾',
    [DependencyType.API]: '🔌',
    [DependencyType.WEBSOCKET]: '🔗',
    [DependencyType.MESSAGE_QUEUE]: '📬',
    [DependencyType.FILE_SYSTEM]: '📁',
    [DependencyType.EXTERNAL_SERVICE]: '🌐'
  };
  
  return icons[type] || '🔧';
}

/**
 * Format response time for display
 */
export function formatResponseTime(ms?: number): string {
  if (ms === undefined || ms === null) return 'N/A';
  
  if (ms < 1) {
    return `${(ms * 1000).toFixed(0)}μs`;
  } else if (ms < 1000) {
    return `${ms.toFixed(1)}ms`;
  } else {
    return `${(ms / 1000).toFixed(2)}s`;
  }
}

/**
 * Format uptime for display
 */
export function formatUptime(seconds?: number): string {
  if (!seconds) return 'N/A';
  
  const days = Math.floor(seconds / 86400);
  const hours = Math.floor((seconds % 86400) / 3600);
  const minutes = Math.floor((seconds % 3600) / 60);
  const secs = Math.floor(seconds % 60);
  
  if (days > 0) {
    return `${days}d ${hours}h ${minutes}m`;
  } else if (hours > 0) {
    return `${hours}h ${minutes}m`;
  } else if (minutes > 0) {
    return `${minutes}m ${secs}s`;
  } else {
    return `${secs}s`;
  }
}


import React from 'react';
import { StatusIndicator, StatusBadge, TrendIndicator } from './StatusIndicator';
import { useThemeAware } from '../contexts/ThemeContext';

export interface HealthMetric {
  id: string;
  label: string;
  value: number | string;
  unit?: string;
  status: 'healthy' | 'warning' | 'error' | 'unknown';
  trend?: 'up' | 'down' | 'stable';
  trendValue?: number;
  lastUpdated: Date;
  threshold?: {
    warning: number;
    error: number;
  };
  description?: string;
}

export interface HealthMetricsProps {
  metrics: HealthMetric[];
  title?: string;
  className?: string;
  layout?: 'grid' | 'list' | 'cards';
  showTrends?: boolean;
  showThresholds?: boolean;
}

export const HealthMetrics: React.FC<HealthMetricsProps> = ({
  metrics,
  title,
  className = '',
  layout = 'grid',
  showTrends = true,
  showThresholds = false,
}) => {
  const { isDark } = useThemeAware();

  const getLayoutClasses = () => {
    switch (layout) {
      case 'list':
        return 'space-y-3';
      case 'cards':
        return 'grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4';
      default: // grid
        return 'grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4';
    }
  };

  const renderMetric = (metric: HealthMetric) => {
    const displayValue = metric.unit ? `${metric.value}${metric.unit}` : metric.value;
    
    return (
      <StatusIndicator
        key={metric.id}
        status={metric.status}
        label={metric.label}
        value={displayValue}
        trend={metric.trend}
        lastUpdated={metric.lastUpdated}
        showTrend={showTrends}
        size="md"
        variant="card"
      />
    );
  };

  return (
    <div className={`bg-design-surface rounded-design-lg shadow-design-md p-6 ${className}`}>
      {title && (
        <h3 className="text-lg font-semibold text-design-text mb-4">{title}</h3>
      )}
      
      <div className={getLayoutClasses()}>
        {metrics.map(renderMetric)}
      </div>
    </div>
  );
};

// Progress Bar Component
export interface ProgressBarProps {
  value: number;
  max?: number;
  label?: string;
  status?: 'healthy' | 'warning' | 'error' | 'unknown';
  showPercentage?: boolean;
  className?: string;
}

export const ProgressBar: React.FC<ProgressBarProps> = ({
  value,
  max = 100,
  label,
  status = 'healthy',
  showPercentage = true,
  className = '',
}) => {
  const percentage = Math.min((value / max) * 100, 100);
  
  const getStatusColor = () => {
    switch (status) {
      case 'healthy':
        return 'bg-design-success';
      case 'warning':
        return 'bg-design-warning';
      case 'error':
        return 'bg-design-error';
      case 'unknown':
        return 'bg-design-text-tertiary';
    }
  };

  return (
    <div className={`w-full ${className}`}>
      {label && (
        <div className="flex justify-between items-center mb-2">
          <span className="text-sm font-medium text-design-text">{label}</span>
          {showPercentage && (
            <span className="text-sm text-design-text-secondary">{percentage.toFixed(1)}%</span>
          )}
        </div>
      )}
      
      <div className="w-full bg-design-background-secondary rounded-full h-2">
        <div
          className={`h-2 rounded-full transition-all duration-design-normal ${getStatusColor()}`}
          style={{ width: `${percentage}%` }}
        />
      </div>
    </div>
  );
};

// Gauge Component
export interface GaugeProps {
  value: number;
  max?: number;
  label?: string;
  status?: 'healthy' | 'warning' | 'error' | 'unknown';
  size?: 'sm' | 'md' | 'lg';
  className?: string;
}

export const Gauge: React.FC<GaugeProps> = ({
  value,
  max = 100,
  label,
  status = 'healthy',
  size = 'md',
  className = '',
}) => {
  const percentage = Math.min((value / max) * 100, 100);
  const angle = (percentage / 100) * 180; // Half circle gauge
  
  const getSizeClasses = () => {
    switch (size) {
      case 'sm':
        return 'w-16 h-8';
      case 'lg':
        return 'w-32 h-16';
      default: // md
        return 'w-24 h-12';
    }
  };

  const getStatusColor = () => {
    switch (status) {
      case 'healthy':
        return '#10B981';
      case 'warning':
        return '#F59E0B';
      case 'error':
        return '#EF4444';
      case 'unknown':
        return '#6B7280';
    }
  };

  return (
    <div className={`flex flex-col items-center ${className}`}>
      {label && (
        <span className="text-sm font-medium text-design-text mb-2">{label}</span>
      )}
      
      <div className={`relative ${getSizeClasses()}`}>
        <svg className="w-full h-full" viewBox="0 0 100 50">
          {/* Background arc */}
          <path
            d="M 10 40 A 40 40 0 0 1 90 40"
            fill="none"
            stroke="var(--color-border)"
            strokeWidth="8"
            strokeLinecap="round"
          />
          
          {/* Progress arc */}
          <path
            d="M 10 40 A 40 40 0 0 1 90 40"
            fill="none"
            stroke={getStatusColor()}
            strokeWidth="8"
            strokeLinecap="round"
            strokeDasharray={`${angle * 0.628} 125.6`}
            strokeDashoffset="0"
            className="transition-all duration-design-normal"
          />
        </svg>
        
        {/* Value text */}
        <div className="absolute inset-0 flex items-center justify-center">
          <span className="text-sm font-bold text-design-text">
            {percentage.toFixed(0)}%
          </span>
        </div>
      </div>
    </div>
  );
};

// Metric Card Component
export interface MetricCardProps {
  title: string;
  value: string | number;
  unit?: string;
  status: 'healthy' | 'warning' | 'error' | 'unknown';
  trend?: 'up' | 'down' | 'stable';
  trendValue?: number;
  lastUpdated: Date;
  description?: string;
  onClick?: () => void;
  className?: string;
}

export const MetricCard: React.FC<MetricCardProps> = ({
  title,
  value,
  unit,
  status,
  trend,
  trendValue,
  lastUpdated,
  description,
  onClick,
  className = '',
}) => {
  const displayValue = unit ? `${value}${unit}` : value;

  return (
    <div 
      className={`
        bg-design-surface rounded-design-lg shadow-design-md p-4 border border-design-border
        hover:shadow-design-lg transition-all duration-design-normal
        ${onClick ? 'cursor-pointer hover:scale-105' : ''}
        ${className}
      `}
      onClick={onClick}
    >
      <div className="flex items-center justify-between mb-2">
        <h4 className="text-sm font-medium text-design-text">{title}</h4>
        <StatusBadge status={status} text={status.toUpperCase()} size="sm" />
      </div>
      
      <div className="text-2xl font-bold text-design-text mb-1">
        {displayValue}
      </div>
      
      {trend && (
        <div className="flex items-center space-x-1 mb-2">
          <TrendIndicator trend={trend} value={trendValue} />
        </div>
      )}
      
      {description && (
        <p className="text-xs text-design-text-secondary mb-2">{description}</p>
      )}
      
      <div className="text-xs text-design-text-tertiary">
        Updated: {lastUpdated.toLocaleTimeString()}
      </div>
    </div>
  );
};

// System Status Overview Component
export interface SystemStatusOverviewProps {
  overallStatus: 'healthy' | 'warning' | 'error' | 'unknown';
  services: Array<{
    name: string;
    status: 'healthy' | 'warning' | 'error' | 'unknown';
    lastChecked: Date;
  }>;
  className?: string;
}

export const SystemStatusOverview: React.FC<SystemStatusOverviewProps> = ({
  overallStatus,
  services,
  className = '',
}) => {
  const getOverallStatusColor = () => {
    switch (overallStatus) {
      case 'healthy':
        return 'bg-design-success-light border-design-success text-design-success-dark';
      case 'warning':
        return 'bg-design-warning-light border-design-warning text-design-warning-dark';
      case 'error':
        return 'bg-design-error-light border-design-error text-design-error-dark';
      case 'unknown':
        return 'bg-design-background-tertiary border-design-border text-design-text-tertiary';
    }
  };

  return (
    <div className={`bg-design-surface rounded-design-lg shadow-design-md p-6 ${className}`}>
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-semibold text-design-text">System Status</h3>
        <div className={`px-3 py-1 rounded-design-md border font-medium ${getOverallStatusColor()}`}>
          {overallStatus.toUpperCase()}
        </div>
      </div>
      
      <div className="space-y-3">
        {services.map((service) => (
          <div key={service.name} className="flex items-center justify-between">
            <span className="text-sm text-design-text">{service.name}</span>
            <div className="flex items-center space-x-2">
              <StatusBadge status={service.status} text={service.status.toUpperCase()} size="sm" />
              <span className="text-xs text-design-text-tertiary">
                {service.lastChecked.toLocaleTimeString()}
              </span>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

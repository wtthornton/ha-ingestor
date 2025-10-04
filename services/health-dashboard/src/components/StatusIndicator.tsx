import React from 'react';
import { 
  CheckCircleIcon, 
  ExclamationTriangleIcon, 
  XCircleIcon, 
  QuestionMarkCircleIcon,
  ArrowUpIcon,
  ArrowDownIcon,
  MinusIcon
} from '@heroicons/react/24/outline';
import { useThemeAware } from '../contexts/ThemeContext';

export type StatusType = 'healthy' | 'warning' | 'error' | 'unknown';
export type TrendType = 'up' | 'down' | 'stable';

export interface StatusIndicatorProps {
  status: StatusType;
  label: string;
  value: string | number;
  trend?: TrendType;
  lastUpdated: Date;
  onClick?: () => void;
  className?: string;
  showTrend?: boolean;
  showLastUpdated?: boolean;
  size?: 'sm' | 'md' | 'lg';
  variant?: 'card' | 'inline' | 'minimal';
}

export const StatusIndicator: React.FC<StatusIndicatorProps> = ({
  status,
  label,
  value,
  trend,
  lastUpdated,
  onClick,
  className = '',
  showTrend = true,
  showLastUpdated = true,
  size = 'md',
  variant = 'card',
}) => {
  const { isDark } = useThemeAware();

  const getStatusIcon = (status: StatusType) => {
    const iconClass = size === 'sm' ? 'h-4 w-4' : size === 'lg' ? 'h-8 w-8' : 'h-6 w-6';
    
    switch (status) {
      case 'healthy':
        return <CheckCircleIcon className={`${iconClass} text-design-success`} />;
      case 'warning':
        return <ExclamationTriangleIcon className={`${iconClass} text-design-warning`} />;
      case 'error':
        return <XCircleIcon className={`${iconClass} text-design-error`} />;
      case 'unknown':
        return <QuestionMarkCircleIcon className={`${iconClass} text-design-text-tertiary`} />;
    }
  };

  const getStatusColors = (status: StatusType) => {
    switch (status) {
      case 'healthy':
        return {
          bg: 'bg-design-success-light',
          text: 'text-design-success-dark',
          border: 'border-design-success',
          icon: 'text-design-success',
        };
      case 'warning':
        return {
          bg: 'bg-design-warning-light',
          text: 'text-design-warning-dark',
          border: 'border-design-warning',
          icon: 'text-design-warning',
        };
      case 'error':
        return {
          bg: 'bg-design-error-light',
          text: 'text-design-error-dark',
          border: 'border-design-error',
          icon: 'text-design-error',
        };
      case 'unknown':
        return {
          bg: 'bg-design-background-tertiary',
          text: 'text-design-text-tertiary',
          border: 'border-design-border',
          icon: 'text-design-text-tertiary',
        };
    }
  };

  const getTrendIcon = (trend: TrendType) => {
    const iconClass = size === 'sm' ? 'h-3 w-3' : 'h-4 w-4';
    
    switch (trend) {
      case 'up':
        return <ArrowUpIcon className={`${iconClass} text-design-success`} />;
      case 'down':
        return <ArrowDownIcon className={`${iconClass} text-design-error`} />;
      case 'stable':
        return <MinusIcon className={`${iconClass} text-design-text-secondary`} />;
    }
  };

  const getSizeClasses = () => {
    switch (size) {
      case 'sm':
        return {
          container: 'p-3',
          label: 'text-xs',
          value: 'text-lg',
          trend: 'text-xs',
          updated: 'text-xs',
        };
      case 'lg':
        return {
          container: 'p-6',
          label: 'text-base',
          value: 'text-3xl',
          trend: 'text-sm',
          updated: 'text-sm',
        };
      default: // md
        return {
          container: 'p-4',
          label: 'text-sm',
          value: 'text-2xl',
          trend: 'text-xs',
          updated: 'text-xs',
        };
    }
  };

  const sizeClasses = getSizeClasses();
  const statusColors = getStatusColors(status);

  if (variant === 'inline') {
    return (
      <div 
        className={`
          flex items-center space-x-2 ${className}
          ${onClick ? 'cursor-pointer hover:opacity-80 transition-opacity duration-design-fast' : ''}
        `}
        onClick={onClick}
      >
        {getStatusIcon(status)}
        <span className={`${sizeClasses.label} font-medium text-design-text`}>{label}</span>
        <span className={`${sizeClasses.value} font-bold ${statusColors.text}`}>{value}</span>
        {trend && showTrend && (
          <div className="flex items-center space-x-1">
            {getTrendIcon(trend)}
          </div>
        )}
      </div>
    );
  }

  if (variant === 'minimal') {
    return (
      <div 
        className={`
          flex items-center space-x-1 ${className}
          ${onClick ? 'cursor-pointer hover:opacity-80 transition-opacity duration-design-fast' : ''}
        `}
        onClick={onClick}
      >
        {getStatusIcon(status)}
        <span className={`${sizeClasses.label} ${statusColors.text}`}>{value}</span>
      </div>
    );
  }

  // Default card variant
  return (
    <div 
      className={`
        ${sizeClasses.container} rounded-design-lg border shadow-design-sm
        ${statusColors.bg} ${statusColors.border}
        hover:shadow-design-md transition-all duration-design-normal
        ${onClick ? 'cursor-pointer hover:scale-105' : ''}
        ${className}
      `}
      onClick={onClick}
    >
      <div className="flex items-center justify-between mb-2">
        <div className="flex items-center space-x-2">
          {getStatusIcon(status)}
          <span className={`${sizeClasses.label} font-medium ${statusColors.text}`}>
            {label}
          </span>
        </div>
        {trend && showTrend && (
          <div className="flex items-center space-x-1">
            {getTrendIcon(trend)}
          </div>
        )}
      </div>
      
      <div className={`${sizeClasses.value} font-bold ${statusColors.text} mb-1`}>
        {value}
      </div>
      
      {showLastUpdated && (
        <div className={`${sizeClasses.updated} opacity-75 ${statusColors.text}`}>
          Updated: {lastUpdated.toLocaleTimeString()}
        </div>
      )}
    </div>
  );
};

// Trend Indicator Component
export interface TrendIndicatorProps {
  trend: TrendType;
  value?: number;
  className?: string;
}

export const TrendIndicator: React.FC<TrendIndicatorProps> = ({ 
  trend, 
  value, 
  className = '' 
}) => {
  const getTrendColor = () => {
    switch (trend) {
      case 'up':
        return 'text-design-success';
      case 'down':
        return 'text-design-error';
      case 'stable':
        return 'text-design-text-secondary';
    }
  };

  const getTrendIcon = () => {
    switch (trend) {
      case 'up':
        return <ArrowUpIcon className="h-4 w-4" />;
      case 'down':
        return <ArrowDownIcon className="h-4 w-4" />;
      case 'stable':
        return <MinusIcon className="h-4 w-4" />;
    }
  };

  return (
    <div className={`flex items-center space-x-1 ${getTrendColor()} ${className}`}>
      {getTrendIcon()}
      {value !== undefined && (
        <span className="text-sm font-medium">{value}%</span>
      )}
    </div>
  );
};

// Status Badge Component
export interface StatusBadgeProps {
  status: StatusType;
  text: string;
  size?: 'sm' | 'md' | 'lg';
  className?: string;
}

export const StatusBadge: React.FC<StatusBadgeProps> = ({ 
  status, 
  text, 
  size = 'md',
  className = '' 
}) => {
  const getStatusColors = () => {
    switch (status) {
      case 'healthy':
        return 'bg-design-success-light text-design-success-dark border-design-success';
      case 'warning':
        return 'bg-design-warning-light text-design-warning-dark border-design-warning';
      case 'error':
        return 'bg-design-error-light text-design-error-dark border-design-error';
      case 'unknown':
        return 'bg-design-background-tertiary text-design-text-tertiary border-design-border';
    }
  };

  const getSizeClasses = () => {
    switch (size) {
      case 'sm':
        return 'px-2 py-1 text-xs';
      case 'lg':
        return 'px-4 py-2 text-base';
      default: // md
        return 'px-3 py-1 text-sm';
    }
  };

  return (
    <span 
      className={`
        inline-flex items-center rounded-design-md border font-medium
        ${getStatusColors()}
        ${getSizeClasses()}
        ${className}
      `}
    >
      {text}
    </span>
  );
};

// Progress Bar Component
export interface ProgressBarProps {
  value: number;
  max?: number;
  size?: 'sm' | 'md' | 'lg';
  variant?: 'default' | 'success' | 'warning' | 'error';
  showLabel?: boolean;
  label?: string;
  className?: string;
}

export const ProgressBar: React.FC<ProgressBarProps> = ({
  value,
  max = 100,
  size = 'md',
  variant = 'default',
  showLabel = false,
  label,
  className = ''
}) => {
  const percentage = Math.min(Math.max((value / max) * 100, 0), 100);

  const getSizeClasses = () => {
    switch (size) {
      case 'sm':
        return 'h-2';
      case 'lg':
        return 'h-4';
      default: // md
        return 'h-3';
    }
  };

  const getVariantClasses = () => {
    switch (variant) {
      case 'success':
        return 'bg-design-success';
      case 'warning':
        return 'bg-design-warning';
      case 'error':
        return 'bg-design-error';
      default:
        return 'bg-design-primary';
    }
  };

  const getBackgroundClasses = () => {
    switch (variant) {
      case 'success':
        return 'bg-design-success-light';
      case 'warning':
        return 'bg-design-warning-light';
      case 'error':
        return 'bg-design-error-light';
      default:
        return 'bg-design-background-secondary';
    }
  };

  return (
    <div className={`w-full ${className}`}>
      {showLabel && label && (
        <div className="flex justify-between items-center mb-1">
          <span className="text-sm text-design-text-secondary">{label}</span>
          <span className="text-sm font-medium text-design-text">{percentage.toFixed(1)}%</span>
        </div>
      )}
      <div className={`w-full ${getBackgroundClasses()} rounded-full overflow-hidden ${getSizeClasses()}`}>
        <div
          className={`${getVariantClasses()} ${getSizeClasses()} transition-all duration-300 ease-out rounded-full`}
          style={{ width: `${percentage}%` }}
        />
      </div>
    </div>
  );
};
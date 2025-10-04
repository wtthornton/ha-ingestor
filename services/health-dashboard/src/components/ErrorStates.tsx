import React from 'react';
import { 
  ExclamationTriangleIcon, 
  XCircleIcon, 
  InformationCircleIcon,
  ArrowPathIcon,
  WifiIcon,
  ServerIcon
} from '@heroicons/react/24/outline';
import { useThemeAware } from '../contexts/ThemeContext';

export type ErrorSeverity = 'error' | 'warning' | 'info';

export interface ErrorStateProps {
  title: string;
  message: string;
  severity: ErrorSeverity;
  onRetry?: () => void;
  onDismiss?: () => void;
  showRetry?: boolean;
  showDismiss?: boolean;
  className?: string;
  icon?: React.ReactNode;
}

export const ErrorState: React.FC<ErrorStateProps> = ({
  title,
  message,
  severity,
  onRetry,
  onDismiss,
  showRetry = true,
  showDismiss = false,
  className = '',
  icon,
}) => {
  const { isDark } = useThemeAware();

  const getSeverityColors = () => {
    switch (severity) {
      case 'error':
        return {
          bg: 'bg-design-error-light',
          border: 'border-design-error',
          text: 'text-design-error-dark',
          icon: 'text-design-error',
        };
      case 'warning':
        return {
          bg: 'bg-design-warning-light',
          border: 'border-design-warning',
          text: 'text-design-warning-dark',
          icon: 'text-design-warning',
        };
      case 'info':
        return {
          bg: 'bg-design-info-light',
          border: 'border-design-info',
          text: 'text-design-info-dark',
          icon: 'text-design-info',
        };
    }
  };

  const getDefaultIcon = () => {
    switch (severity) {
      case 'error':
        return <XCircleIcon className="h-6 w-6" />;
      case 'warning':
        return <ExclamationTriangleIcon className="h-6 w-6" />;
      case 'info':
        return <InformationCircleIcon className="h-6 w-6" />;
    }
  };

  const colors = getSeverityColors();
  const displayIcon = icon || getDefaultIcon();

  return (
    <div className={`
      ${colors.bg} ${colors.border} border rounded-design-lg p-4
      ${className}
    `}>
      <div className="flex items-start space-x-3">
        <div className={`flex-shrink-0 ${colors.icon}`}>
          {displayIcon}
        </div>
        
        <div className="flex-1 min-w-0">
          <h3 className={`text-sm font-medium ${colors.text}`}>
            {title}
          </h3>
          <p className={`mt-1 text-sm ${colors.text}`}>
            {message}
          </p>
          
          {(showRetry || showDismiss) && (
            <div className="mt-3 flex space-x-2">
              {showRetry && onRetry && (
                <button
                  onClick={onRetry}
                  className={`
                    inline-flex items-center space-x-1 px-3 py-1 rounded-design-md text-sm font-medium
                    ${colors.text} hover:opacity-80 transition-opacity duration-design-fast
                  `}
                >
                  <ArrowPathIcon className="h-4 w-4" />
                  <span>Retry</span>
                </button>
              )}
              
              {showDismiss && onDismiss && (
                <button
                  onClick={onDismiss}
                  className={`
                    inline-flex items-center px-3 py-1 rounded-design-md text-sm font-medium
                    ${colors.text} hover:opacity-80 transition-opacity duration-design-fast
                  `}
                >
                  Dismiss
                </button>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

// Connection Error Component
export interface ConnectionErrorProps {
  service: string;
  onRetry?: () => void;
  className?: string;
}

export const ConnectionError: React.FC<ConnectionErrorProps> = ({
  service,
  onRetry,
  className = '',
}) => {
  return (
    <ErrorState
      title={`${service} Connection Failed`}
      message={`Unable to connect to ${service}. Please check your connection and try again.`}
      severity="error"
      onRetry={onRetry}
      showRetry={true}
      icon={<WifiIcon className="h-6 w-6" />}
      className={className}
    />
  );
};

// Service Error Component
export interface ServiceErrorProps {
  service: string;
  error: string;
  onRetry?: () => void;
  className?: string;
}

export const ServiceError: React.FC<ServiceErrorProps> = ({
  service,
  error,
  onRetry,
  className = '',
}) => {
  return (
    <ErrorState
      title={`${service} Error`}
      message={error}
      severity="error"
      onRetry={onRetry}
      showRetry={true}
      icon={<ServerIcon className="h-6 w-6" />}
      className={className}
    />
  );
};

// Warning State Component
export interface WarningStateProps {
  title: string;
  message: string;
  onDismiss?: () => void;
  className?: string;
}

export const WarningState: React.FC<WarningStateProps> = ({
  title,
  message,
  onDismiss,
  className = '',
}) => {
  return (
    <ErrorState
      title={title}
      message={message}
      severity="warning"
      onDismiss={onDismiss}
      showDismiss={true}
      className={className}
    />
  );
};

// Info State Component
export interface InfoStateProps {
  title: string;
  message: string;
  onDismiss?: () => void;
  className?: string;
}

export const InfoState: React.FC<InfoStateProps> = ({
  title,
  message,
  onDismiss,
  className = '',
}) => {
  return (
    <ErrorState
      title={title}
      message={message}
      severity="info"
      onDismiss={onDismiss}
      showDismiss={true}
      className={className}
    />
  );
};

// Empty State Component
export interface EmptyStateProps {
  title: string;
  message: string;
  icon?: React.ReactNode;
  action?: {
    label: string;
    onClick: () => void;
  };
  className?: string;
}

export const EmptyState: React.FC<EmptyStateProps> = ({
  title,
  message,
  icon,
  action,
  className = '',
}) => {
  return (
    <div className={`text-center py-8 ${className}`}>
      {icon && (
        <div className="mx-auto h-12 w-12 text-design-text-tertiary mb-4">
          {icon}
        </div>
      )}
      
      <h3 className="text-lg font-medium text-design-text mb-2">
        {title}
      </h3>
      
      <p className="text-design-text-secondary mb-4">
        {message}
      </p>
      
      {action && (
        <button
          onClick={action.onClick}
          className="
            inline-flex items-center px-4 py-2 border border-design-border rounded-design-md
            text-sm font-medium text-design-text bg-design-surface
            hover:bg-design-surface-hover focus:outline-none focus:ring-2 focus:ring-design-border-focus
            transition-colors duration-design-fast
          "
        >
          {action.label}
        </button>
      )}
    </div>
  );
};

// Loading Error Component
export interface LoadingErrorProps {
  onRetry?: () => void;
  className?: string;
}

export const LoadingError: React.FC<LoadingErrorProps> = ({
  onRetry,
  className = '',
}) => {
  return (
    <ErrorState
      title="Failed to Load Data"
      message="There was an error loading the data. Please try again."
      severity="error"
      onRetry={onRetry}
      showRetry={true}
      className={className}
    />
  );
};

// Network Error Component
export interface NetworkErrorProps {
  onRetry?: () => void;
  className?: string;
}

export const NetworkError: React.FC<NetworkErrorProps> = ({
  onRetry,
  className = '',
}) => {
  return (
    <ErrorState
      title="Network Error"
      message="Unable to connect to the server. Please check your internet connection."
      severity="error"
      onRetry={onRetry}
      showRetry={true}
      icon={<WifiIcon className="h-6 w-6" />}
      className={className}
    />
  );
};

// Alert Banner Component
export interface AlertBannerProps {
  message: string;
  severity: ErrorSeverity;
  onDismiss?: () => void;
  className?: string;
}

export const AlertBanner: React.FC<AlertBannerProps> = ({
  message,
  severity,
  onDismiss,
  className = '',
}) => {
  const getSeverityColors = () => {
    switch (severity) {
      case 'error':
        return 'bg-design-error-light border-design-error text-design-error-dark';
      case 'warning':
        return 'bg-design-warning-light border-design-warning text-design-warning-dark';
      case 'info':
        return 'bg-design-info-light border-design-info text-design-info-dark';
    }
  };

  const getIcon = () => {
    switch (severity) {
      case 'error':
        return <XCircleIcon className="h-5 w-5" />;
      case 'warning':
        return <ExclamationTriangleIcon className="h-5 w-5" />;
      case 'info':
        return <InformationCircleIcon className="h-5 w-5" />;
    }
  };

  return (
    <div className={`
      ${getSeverityColors()} border rounded-design-md p-3
      ${className}
    `}>
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-2">
          {getIcon()}
          <span className="text-sm font-medium">{message}</span>
        </div>
        
        {onDismiss && (
          <button
            onClick={onDismiss}
            className="text-sm hover:opacity-80 transition-opacity duration-design-fast"
          >
            Dismiss
          </button>
        )}
      </div>
    </div>
  );
};

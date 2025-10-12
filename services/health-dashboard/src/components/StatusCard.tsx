import React from 'react';

interface StatusCardProps {
  title: string;
  status: 'healthy' | 'degraded' | 'unhealthy' | 'connected' | 'disconnected';
  value?: string | number;
  subtitle?: string;
  className?: string;
}

const getStatusColor = (status: string) => {
  switch (status) {
    case 'healthy':
    case 'connected':
      return 'bg-green-100 dark:bg-green-900 text-green-800 dark:text-green-200 border-green-200 dark:border-green-700';
    case 'degraded':
      return 'bg-yellow-100 dark:bg-yellow-900 text-yellow-800 dark:text-yellow-200 border-yellow-200 dark:border-yellow-700';
    case 'unhealthy':
    case 'disconnected':
      return 'bg-red-100 dark:bg-red-900 text-red-800 dark:text-red-200 border-red-200 dark:border-red-700';
    default:
      return 'bg-gray-100 dark:bg-gray-700 text-gray-800 dark:text-gray-200 border-gray-200 dark:border-gray-600';
  }
};

const getStatusIcon = (status: string) => {
  switch (status) {
    case 'healthy':
    case 'connected':
      return '✅';
    case 'degraded':
      return '⚠️';
    case 'unhealthy':
    case 'disconnected':
      return '❌';
    default:
      return '❓';
  }
};

export const StatusCard: React.FC<StatusCardProps> = ({
  title,
  status,
  value,
  subtitle,
  className = ''
}) => {
  return (
    <div className={`
      card-base content-fade-in p-6 
      ${className}
    `}>
      <div className="flex items-center justify-between mb-2">
        <h3 className="text-sm font-medium text-gray-900 dark:text-gray-100">{title}</h3>
        <span className="text-lg icon-entrance">{getStatusIcon(status)}</span>
      </div>
      
      <div className="flex items-center justify-between">
        <div>
          {value && (
            <p className="text-2xl font-bold text-gray-900 dark:text-gray-100 number-count">{value}</p>
          )}
          {subtitle && (
            <p className="text-small">{subtitle}</p>
          )}
        </div>
        
        <span className={`
          px-2 py-1 text-xs font-medium rounded-full border status-transition
          ${getStatusColor(status)}
        `}>
          {status}
        </span>
      </div>
    </div>
  );
};

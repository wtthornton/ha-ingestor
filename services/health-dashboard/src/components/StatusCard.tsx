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
      return 'bg-green-100 text-green-800 border-green-200';
    case 'degraded':
      return 'bg-yellow-100 text-yellow-800 border-yellow-200';
    case 'unhealthy':
    case 'disconnected':
      return 'bg-red-100 text-red-800 border-red-200';
    default:
      return 'bg-gray-100 text-gray-800 border-gray-200';
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
    <div className={`bg-white rounded-lg shadow-sm border p-6 ${className}`}>
      <div className="flex items-center justify-between mb-2">
        <h3 className="text-sm font-medium text-gray-900">{title}</h3>
        <span className="text-lg">{getStatusIcon(status)}</span>
      </div>
      
      <div className="flex items-center justify-between">
        <div>
          {value && (
            <p className="text-2xl font-bold text-gray-900">{value}</p>
          )}
          {subtitle && (
            <p className="text-sm text-gray-500">{subtitle}</p>
          )}
        </div>
        
        <span className={`px-2 py-1 text-xs font-medium rounded-full border ${getStatusColor(status)}`}>
          {status}
        </span>
      </div>
    </div>
  );
};

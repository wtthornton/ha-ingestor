import React from 'react';

interface DataSourceCardProps {
  title: string;
  icon: string;
  status: 'healthy' | 'degraded' | 'offline';
  value: string | number;
  subtitle: string;
  successRate?: number;
  lastFetch?: string | null;
}

export const DataSourceCard: React.FC<DataSourceCardProps> = ({
  title,
  icon,
  status,
  value,
  subtitle,
  successRate,
  lastFetch
}) => {
  const statusColors = {
    healthy: 'bg-green-100 text-green-800 border-green-200',
    degraded: 'bg-yellow-100 text-yellow-800 border-yellow-200',
    offline: 'bg-red-100 text-red-800 border-red-200'
  };

  const iconColors = {
    healthy: 'text-green-600',
    degraded: 'text-yellow-600',
    offline: 'text-red-600'
  };

  return (
    <div className="bg-white rounded-lg shadow-md p-6 border-l-4 border-transparent hover:shadow-lg transition-shadow">
      <div className="flex items-start justify-between mb-4">
        <div className="flex-1">
          <div className="flex items-center gap-2 mb-2">
            <span className="text-2xl">{icon}</span>
            <h3 className="text-sm font-medium text-gray-600">{title}</h3>
          </div>
          <p className="text-3xl font-bold text-gray-900">{value}</p>
          <p className="text-sm text-gray-500 mt-1">{subtitle}</p>
        </div>
        <div>
          <span className={`px-3 py-1 rounded-full text-xs font-semibold ${statusColors[status]}`}>
            {status}
          </span>
        </div>
      </div>
      
      {successRate !== undefined && (
        <div className="mt-4 pt-4 border-t border-gray-100">
          <div className="flex justify-between items-center text-sm">
            <span className="text-gray-600">Success Rate</span>
            <span className={`font-semibold ${successRate >= 0.95 ? 'text-green-600' : 'text-yellow-600'}`}>
              {(successRate * 100).toFixed(1)}%
            </span>
          </div>
          {lastFetch && (
            <div className="flex justify-between items-center text-xs text-gray-500 mt-2">
              <span>Last Update</span>
              <span>{new Date(lastFetch).toLocaleTimeString()}</span>
            </div>
          )}
        </div>
      )}
    </div>
  );
};


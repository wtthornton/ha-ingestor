import React from 'react';
import type { ServiceStatus } from '../types';

interface ServiceCardProps {
  service: ServiceStatus;
  icon: string;
  darkMode: boolean;
  onViewDetails?: () => void;
  onConfigure?: () => void;
}

export const ServiceCard: React.FC<ServiceCardProps> = ({
  service,
  icon,
  darkMode,
  onViewDetails,
  onConfigure,
}) => {
  const getStatusColor = (status: string) => {
    switch (status) {
      case 'running':
        return darkMode ? 'bg-green-900 text-green-200' : 'bg-green-100 text-green-800';
      case 'stopped':
        return darkMode ? 'bg-gray-700 text-gray-300' : 'bg-gray-100 text-gray-600';
      case 'error':
        return darkMode ? 'bg-red-900 text-red-200' : 'bg-red-100 text-red-800';
      case 'degraded':
        return darkMode ? 'bg-yellow-900 text-yellow-200' : 'bg-yellow-100 text-yellow-800';
      default:
        return darkMode ? 'bg-gray-700 text-gray-300' : 'bg-gray-100 text-gray-600';
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'running':
        return '🟢';
      case 'stopped':
        return '⚪';
      case 'error':
        return '🔴';
      case 'degraded':
        return '🟡';
      default:
        return '⚪';
    }
  };

  return (
    <div
      className={`rounded-lg shadow-md p-6 transition-all duration-200 hover:shadow-lg ${
        darkMode ? 'bg-gray-800 border border-gray-700' : 'bg-white border border-gray-200'
      }`}
    >
      {/* Header */}
      <div className="flex items-start justify-between mb-4">
        <div className="flex items-center space-x-3">
          <div className="text-3xl">{icon}</div>
          <div>
            <h3 className={`font-semibold text-lg ${darkMode ? 'text-white' : 'text-gray-900'}`}>
              {service.service}
            </h3>
            {service.port && (
              <p className={`text-sm ${darkMode ? 'text-gray-400' : 'text-gray-500'}`}>
                Port {service.port}
              </p>
            )}
          </div>
        </div>
        <span className={`flex items-center space-x-1 px-3 py-1 rounded-full text-xs font-medium ${getStatusColor(service.status)}`}>
          <span>{getStatusIcon(service.status)}</span>
          <span className="capitalize">{service.status}</span>
        </span>
      </div>

      {/* Metrics */}
      <div className="space-y-2 mb-4">
        {service.uptime && (
          <div className="flex justify-between items-center">
            <span className={`text-sm ${darkMode ? 'text-gray-400' : 'text-gray-600'}`}>
              Uptime
            </span>
            <span className={`text-sm font-medium ${darkMode ? 'text-white' : 'text-gray-900'}`}>
              {service.uptime}
            </span>
          </div>
        )}
        
        {service.metrics?.requests_per_minute !== undefined && (
          <div className="flex justify-between items-center">
            <span className={`text-sm ${darkMode ? 'text-gray-400' : 'text-gray-600'}`}>
              Requests/min
            </span>
            <span className={`text-sm font-medium ${darkMode ? 'text-white' : 'text-gray-900'}`}>
              {service.metrics.requests_per_minute.toFixed(1)}
            </span>
          </div>
        )}
        
        {service.metrics?.error_rate !== undefined && (
          <div className="flex justify-between items-center">
            <span className={`text-sm ${darkMode ? 'text-gray-400' : 'text-gray-600'}`}>
              Error Rate
            </span>
            <span className={`text-sm font-medium ${
              service.metrics.error_rate > 5 
                ? 'text-red-600' 
                : darkMode ? 'text-green-400' : 'text-green-600'
            }`}>
              {service.metrics.error_rate.toFixed(2)}%
            </span>
          </div>
        )}
      </div>

      {/* Error Message */}
      {service.error && (
        <div className={`mb-4 p-3 rounded-md text-sm ${
          darkMode ? 'bg-red-900/30 text-red-200' : 'bg-red-50 text-red-800'
        }`}>
          {service.error}
        </div>
      )}

      {/* Actions */}
      <div className="flex space-x-2">
        {onViewDetails && (
          <button
            onClick={onViewDetails}
            className={`flex-1 px-3 py-2 rounded-md text-sm font-medium transition-colors duration-200 ${
              darkMode
                ? 'bg-blue-600 hover:bg-blue-700 text-white'
                : 'bg-blue-100 hover:bg-blue-200 text-blue-700'
            }`}
          >
            👁️ View Details
          </button>
        )}
        {onConfigure && (
          <button
            onClick={onConfigure}
            className={`flex-1 px-3 py-2 rounded-md text-sm font-medium transition-colors duration-200 ${
              darkMode
                ? 'bg-gray-700 hover:bg-gray-600 text-white'
                : 'bg-gray-100 hover:bg-gray-200 text-gray-700'
            }`}
          >
            ⚙️ Configure
          </button>
        )}
      </div>
    </div>
  );
};


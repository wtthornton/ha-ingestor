/**
 * AlertsWidget Component
 * 
 * Recent alerts widget for customizable dashboard
 * Epic 15.3: Dashboard Customization & Layout
 */

import React from 'react';

interface AlertsWidgetProps {
  darkMode: boolean;
}

export const AlertsWidget: React.FC<AlertsWidgetProps> = ({ darkMode }) => {
  // Mock alerts for now
  const alerts = [
    { id: '1', severity: 'error', service: 'websocket-ingestion', message: 'Connection timeout', time: '2 min ago' },
    { id: '2', severity: 'warning', service: 'weather-api', message: 'Rate limit approaching', time: '5 min ago' },
    { id: '3', severity: 'info', service: 'influxdb', message: 'Backup completed', time: '15 min ago' }
  ];

  const getSeverityBadge = (severity: string) => {
    switch (severity) {
      case 'error': return 'badge-error';
      case 'warning': return 'badge-warning';
      case 'info': return 'badge-info';
      default: return 'badge-info';
    }
  };

  return (
    <div className="h-full flex flex-col">
      <h3 className={`text-lg font-semibold mb-3 ${darkMode ? 'text-white' : 'text-gray-900'}`}>
        🚨 Recent Alerts
      </h3>
      
      <div className="flex-1 overflow-y-auto space-y-2">
        {alerts.map((alert) => (
          <div
            key={alert.id}
            className={`p-3 rounded-lg border transition-colors ${
              darkMode ? 'border-gray-700 hover:bg-gray-700/50' : 'border-gray-200 hover:bg-gray-50'
            }`}
          >
            <div className="flex items-start justify-between gap-2 mb-1">
              <span className={`badge-base ${getSeverityBadge(alert.severity)} text-xs`}>
                {alert.severity.toUpperCase()}
              </span>
              <span className={`text-xs ${darkMode ? 'text-gray-400' : 'text-gray-500'}`}>
                {alert.time}
              </span>
            </div>
            <p className={`text-sm ${darkMode ? 'text-white' : 'text-gray-900'}`}>
              {alert.message}
            </p>
            <p className={`text-xs mt-1 ${darkMode ? 'text-gray-400' : 'text-gray-500'}`}>
              {alert.service}
            </p>
          </div>
        ))}
      </div>
    </div>
  );
};


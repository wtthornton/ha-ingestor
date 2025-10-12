/**
 * ServicesWidget Component
 * 
 * Services overview widget for customizable dashboard
 * Epic 15.3: Dashboard Customization & Layout
 */

import React, { useState, useEffect } from 'react';

interface ServicesWidgetProps {
  darkMode: boolean;
}

export const ServicesWidget: React.FC<ServicesWidgetProps> = ({ darkMode }) => {
  const [services, setServices] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchServices = async () => {
      try {
        const response = await fetch('/api/v1/services');
        if (response.ok) {
          const data = await response.json();
          setServices(data.services || []);
        }
        setLoading(false);
      } catch (error) {
        console.error('Error fetching services:', error);
        setLoading(false);
      }
    };

    fetchServices();
    const interval = setInterval(fetchServices, 30000);
    return () => clearInterval(interval);
  }, []);

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'running': return '🟢';
      case 'stopped': return '⚪';
      case 'error': return '🔴';
      case 'degraded': return '🟡';
      default: return '⚪';
    }
  };

  const runningCount = services.filter(s => s.status === 'running').length;
  const errorCount = services.filter(s => s.status === 'error').length;

  return (
    <div className="h-full flex flex-col">
      <div className="flex justify-between items-center mb-3">
        <h3 className={`text-lg font-semibold ${darkMode ? 'text-white' : 'text-gray-900'}`}>
          🔧 Services
        </h3>
        <div className="flex gap-2 text-sm">
          <span className={`badge-success`}>{runningCount} Running</span>
          {errorCount > 0 && <span className={`badge-error`}>{errorCount} Errors</span>}
        </div>
      </div>
      
      {loading ? (
        <div className="flex-1 flex items-center justify-center">
          <div className={`animate-spin h-8 w-8 border-2 border-blue-500 border-t-transparent rounded-full`}></div>
        </div>
      ) : (
        <div className="flex-1 overflow-y-auto space-y-2">
          {services.slice(0, 6).map((service) => (
            <div
              key={service.service}
              className={`p-2 rounded-lg border transition-colors ${
                darkMode ? 'border-gray-700 hover:bg-gray-700/50' : 'border-gray-200 hover:bg-gray-50'
              }`}
            >
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2 flex-1 min-w-0">
                  <span className="text-lg">{getStatusIcon(service.status)}</span>
                  <span className={`text-sm font-medium truncate ${darkMode ? 'text-white' : 'text-gray-900'}`}>
                    {service.service}
                  </span>
                </div>
                {service.uptime && (
                  <span className={`text-xs ${darkMode ? 'text-gray-400' : 'text-gray-500'}`}>
                    {service.uptime}
                  </span>
                )}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};


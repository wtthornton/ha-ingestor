import React, { useEffect, useState } from 'react';
import { createPortal } from 'react-dom';
import type {
  ServiceStatus,
  ServiceDetails,
  ServiceLog,
  ServiceResourceUsage,
  ServiceHealthCheck,
} from '../types';

interface ServiceDetailsModalProps {
  service: ServiceStatus;
  icon: string;
  isOpen: boolean;
  onClose: () => void;
  darkMode: boolean;
}

export const ServiceDetailsModal: React.FC<ServiceDetailsModalProps> = ({
  service,
  icon,
  isOpen,
  onClose,
  darkMode,
}) => {
  const [details, setDetails] = useState<ServiceDetails | null>(null);
  const [logs, setLogs] = useState<ServiceLog[]>([]);
  const [resourceUsage, setResourceUsage] = useState<ServiceResourceUsage | null>(null);
  const [healthHistory, setHealthHistory] = useState<ServiceHealthCheck[]>([]);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState<'overview' | 'logs' | 'metrics' | 'health'>('overview');

  // Fetch detailed service data
  useEffect(() => {
    if (!isOpen) return;

    const fetchServiceData = async () => {
      setLoading(true);
      try {
        // Fetch service details (mock data for now)
        const mockDetails: ServiceDetails = {
          service: service.service,
          status: service.status,
          uptime: service.uptime || 'Unknown',
          container_id: `${service.service}-container-${Math.random().toString(36).substr(2, 9)}`,
          image: `ha-ingestor/${service.service}:latest`,
          last_restart: new Date(Date.now() - 2 * 60 * 60 * 1000).toISOString(),
          port_mappings: service.port ? [`${service.port}:${service.port}`] : [],
        };
        setDetails(mockDetails);

        // Fetch logs (mock data)
        const mockLogs: ServiceLog[] = Array.from({ length: 20 }, (_, i) => ({
          timestamp: new Date(Date.now() - (20 - i) * 60000).toISOString(),
          level: ['INFO', 'WARN', 'ERROR', 'DEBUG'][Math.floor(Math.random() * 4)] as ServiceLog['level'],
          message: `Log message ${i + 1} - ${service.service} operation completed successfully`,
        }));
        setLogs(mockLogs);

        // Fetch resource usage (mock data)
        const mockResources: ServiceResourceUsage = {
          cpu_percent: service.metrics?.cpu_usage || Math.random() * 50,
          memory_used_mb: service.metrics?.memory_usage || Math.random() * 256,
          memory_limit_mb: 512,
          memory_percent: ((service.metrics?.memory_usage || Math.random() * 256) / 512) * 100,
        };
        setResourceUsage(mockResources);

        // Fetch health history (mock data)
        const mockHealth: ServiceHealthCheck[] = Array.from({ length: 24 }, (_, i) => ({
          timestamp: new Date(Date.now() - (24 - i) * 60 * 60 * 1000).toISOString(),
          status: Math.random() > 0.1 ? 'healthy' : 'unhealthy',
          response_time: Math.random() * 100,
        }));
        setHealthHistory(mockHealth);

        setLoading(false);
      } catch (error) {
        console.error('Error fetching service data:', error);
        setLoading(false);
      }
    };

    fetchServiceData();
  }, [isOpen, service]);

  // Handle escape key
  useEffect(() => {
    const handleEscape = (e: KeyboardEvent) => {
      if (e.key === 'Escape' && isOpen) {
        onClose();
      }
    };

    document.addEventListener('keydown', handleEscape);
    return () => document.removeEventListener('keydown', handleEscape);
  }, [isOpen, onClose]);

  // Prevent body scroll when modal is open
  useEffect(() => {
    if (isOpen) {
      document.body.style.overflow = 'hidden';
    } else {
      document.body.style.overflow = 'unset';
    }
    return () => {
      document.body.style.overflow = 'unset';
    };
  }, [isOpen]);

  if (!isOpen) return null;

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'running':
        return darkMode ? 'bg-green-900 text-green-200' : 'bg-green-100 text-green-800';
      case 'error':
        return darkMode ? 'bg-red-900 text-red-200' : 'bg-red-100 text-red-800';
      case 'degraded':
        return darkMode ? 'bg-yellow-900 text-yellow-200' : 'bg-yellow-100 text-yellow-800';
      default:
        return darkMode ? 'bg-gray-700 text-gray-300' : 'bg-gray-100 text-gray-600';
    }
  };

  const getLogLevelColor = (level: ServiceLog['level']) => {
    switch (level) {
      case 'ERROR':
        return darkMode ? 'bg-red-900 text-red-200' : 'bg-red-100 text-red-800';
      case 'WARN':
        return darkMode ? 'bg-yellow-900 text-yellow-200' : 'bg-yellow-100 text-yellow-800';
      case 'INFO':
        return darkMode ? 'bg-blue-900 text-blue-200' : 'bg-blue-100 text-blue-800';
      case 'DEBUG':
        return darkMode ? 'bg-gray-700 text-gray-300' : 'bg-gray-100 text-gray-600';
    }
  };

  const getResourceColor = (percent: number) => {
    if (percent >= 90) return 'bg-red-500';
    if (percent >= 70) return 'bg-yellow-500';
    return 'bg-green-500';
  };

  const formatTimestamp = (timestamp: string) => {
    return new Date(timestamp).toLocaleString('en-US', {
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit',
      hour12: true,
    });
  };

  const modalContent = (
    <>
      {/* Backdrop */}
      <div
        className="fixed inset-0 bg-black bg-opacity-50 z-40 transition-opacity"
        onClick={onClose}
      />

      {/* Modal */}
      <div
        className={`fixed inset-0 z-50 flex items-center justify-center p-4 overflow-y-auto`}
        onClick={onClose}
      >
        <div
          className={`relative w-full max-w-6xl max-h-[90vh] rounded-lg shadow-2xl ${
            darkMode ? 'bg-gray-800 text-white' : 'bg-white text-gray-900'
          }`}
          onClick={(e) => e.stopPropagation()}
        >
          {/* Header */}
          <div className={`flex items-center justify-between p-6 border-b ${
            darkMode ? 'border-gray-700' : 'border-gray-200'
          }`}>
            <div className="flex items-center space-x-4">
              <div className="text-4xl">{icon}</div>
              <div>
                <h2 className="text-2xl font-bold">{service.service}</h2>
                <span className={`inline-flex items-center px-3 py-1 rounded-full text-sm font-medium ${getStatusColor(service.status)}`}>
                  {service.status.toUpperCase()}
                </span>
              </div>
            </div>
            <button
              onClick={onClose}
              className={`text-2xl font-bold w-10 h-10 rounded-full transition-colors ${
                darkMode
                  ? 'hover:bg-gray-700 text-gray-400 hover:text-white'
                  : 'hover:bg-gray-100 text-gray-600 hover:text-gray-900'
              }`}
            >
              ×
            </button>
          </div>

          {/* Tabs */}
          <div className={`flex space-x-1 p-4 border-b ${
            darkMode ? 'border-gray-700' : 'border-gray-200'
          }`}>
            {[
              { id: 'overview', label: '📊 Overview' },
              { id: 'logs', label: '📝 Logs' },
              { id: 'metrics', label: '📈 Metrics' },
              { id: 'health', label: '💚 Health' },
            ].map((tab) => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id as typeof activeTab)}
                className={`px-4 py-2 rounded-md font-medium transition-colors ${
                  activeTab === tab.id
                    ? darkMode
                      ? 'bg-blue-600 text-white'
                      : 'bg-blue-100 text-blue-700'
                    : darkMode
                    ? 'text-gray-400 hover:text-white hover:bg-gray-700'
                    : 'text-gray-600 hover:text-gray-900 hover:bg-gray-100'
                }`}
              >
                {tab.label}
              </button>
            ))}
          </div>

          {/* Content */}
          <div className="p-6 overflow-y-auto max-h-[calc(90vh-200px)]">
            {loading ? (
              <div className="flex items-center justify-center h-64">
                <div className={`animate-spin rounded-full h-12 w-12 border-b-2 ${
                  darkMode ? 'border-blue-400' : 'border-blue-600'
                }`}></div>
              </div>
            ) : (
              <>
                {/* Overview Tab */}
                {activeTab === 'overview' && details && resourceUsage && (
                  <div className="space-y-6">
                    {/* Service Info Grid */}
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                      <div className={`p-4 rounded-lg ${darkMode ? 'bg-gray-700' : 'bg-gray-50'}`}>
                        <h3 className="font-semibold mb-3">Service Information</h3>
                        <dl className="space-y-2 text-sm">
                          <div className="flex justify-between">
                            <dt className={darkMode ? 'text-gray-400' : 'text-gray-600'}>Uptime:</dt>
                            <dd className="font-medium">{details.uptime}</dd>
                          </div>
                          <div className="flex justify-between">
                            <dt className={darkMode ? 'text-gray-400' : 'text-gray-600'}>Container ID:</dt>
                            <dd className="font-mono text-xs">{details.container_id?.slice(0, 12)}</dd>
                          </div>
                          <div className="flex justify-between">
                            <dt className={darkMode ? 'text-gray-400' : 'text-gray-600'}>Image:</dt>
                            <dd className="font-mono text-xs">{details.image}</dd>
                          </div>
                          {details.last_restart && (
                            <div className="flex justify-between">
                              <dt className={darkMode ? 'text-gray-400' : 'text-gray-600'}>Last Restart:</dt>
                              <dd className="text-xs">{new Date(details.last_restart).toLocaleString()}</dd>
                            </div>
                          )}
                        </dl>
                      </div>

                      <div className={`p-4 rounded-lg ${darkMode ? 'bg-gray-700' : 'bg-gray-50'}`}>
                        <h3 className="font-semibold mb-3">Resource Usage</h3>
                        <div className="space-y-4">
                          {/* CPU Usage */}
                          <div>
                            <div className="flex justify-between text-sm mb-1">
                              <span className={darkMode ? 'text-gray-400' : 'text-gray-600'}>CPU</span>
                              <span className="font-medium">{resourceUsage.cpu_percent.toFixed(1)}%</span>
                            </div>
                            <div className={`w-full h-2 rounded-full ${darkMode ? 'bg-gray-600' : 'bg-gray-200'}`}>
                              <div
                                className={`h-full rounded-full transition-all ${getResourceColor(resourceUsage.cpu_percent)}`}
                                style={{ width: `${Math.min(resourceUsage.cpu_percent, 100)}%` }}
                              />
                            </div>
                          </div>

                          {/* Memory Usage */}
                          <div>
                            <div className="flex justify-between text-sm mb-1">
                              <span className={darkMode ? 'text-gray-400' : 'text-gray-600'}>Memory</span>
                              <span className="font-medium">
                                {resourceUsage.memory_used_mb.toFixed(0)}MB / {resourceUsage.memory_limit_mb}MB
                                ({resourceUsage.memory_percent.toFixed(1)}%)
                              </span>
                            </div>
                            <div className={`w-full h-2 rounded-full ${darkMode ? 'bg-gray-600' : 'bg-gray-200'}`}>
                              <div
                                className={`h-full rounded-full transition-all ${getResourceColor(resourceUsage.memory_percent)}`}
                                style={{ width: `${Math.min(resourceUsage.memory_percent, 100)}%` }}
                              />
                            </div>
                          </div>
                        </div>
                      </div>
                    </div>

                    {/* Port Mappings */}
                    {details.port_mappings && details.port_mappings.length > 0 && (
                      <div className={`p-4 rounded-lg ${darkMode ? 'bg-gray-700' : 'bg-gray-50'}`}>
                        <h3 className="font-semibold mb-3">Port Mappings</h3>
                        <div className="flex flex-wrap gap-2">
                          {details.port_mappings.map((port, i) => (
                            <span
                              key={i}
                              className={`px-3 py-1 rounded-md text-sm font-mono ${
                                darkMode ? 'bg-gray-600 text-gray-200' : 'bg-gray-200 text-gray-700'
                              }`}
                            >
                              {port}
                            </span>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                )}

                {/* Logs Tab */}
                {activeTab === 'logs' && (
                  <div className={`rounded-lg border ${darkMode ? 'bg-gray-900 border-gray-700' : 'bg-gray-50 border-gray-200'}`}>
                    <div className={`p-4 border-b ${darkMode ? 'border-gray-700' : 'border-gray-200'} flex justify-between items-center`}>
                      <h3 className="font-semibold">Recent Logs (Last 20)</h3>
                      <button
                        className={`px-3 py-1 rounded-md text-sm transition-colors ${
                          darkMode
                            ? 'bg-blue-600 hover:bg-blue-700 text-white'
                            : 'bg-blue-100 hover:bg-blue-200 text-blue-700'
                        }`}
                      >
                        📋 Copy Logs
                      </button>
                    </div>
                    <div className="p-4 font-mono text-sm space-y-2 max-h-96 overflow-y-auto">
                      {logs.map((log, i) => (
                        <div key={i} className="flex items-start space-x-3">
                          <span className={darkMode ? 'text-gray-500' : 'text-gray-400'}>
                            {formatTimestamp(log.timestamp)}
                          </span>
                          <span className={`px-2 py-0.5 rounded text-xs font-medium ${getLogLevelColor(log.level)}`}>
                            {log.level}
                          </span>
                          <span className="flex-1">{log.message}</span>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* Metrics Tab */}
                {activeTab === 'metrics' && (
                  <div className={`p-8 rounded-lg text-center ${darkMode ? 'bg-gray-700' : 'bg-gray-50'}`}>
                    <div className="text-6xl mb-4">📈</div>
                    <h3 className="text-xl font-bold mb-2">Metrics Charts</h3>
                    <p className={`mb-4 ${darkMode ? 'text-gray-400' : 'text-gray-600'}`}>
                      Real-time metrics visualization
                    </p>
                    <div className={`p-4 rounded-md text-left ${darkMode ? 'bg-gray-800' : 'bg-white'}`}>
                      <p className="text-sm font-medium mb-2">📦 Installation Required:</p>
                      <code className={`block p-3 rounded text-xs ${darkMode ? 'bg-gray-900' : 'bg-gray-100'}`}>
                        npm install chart.js react-chartjs-2
                      </code>
                      <p className="text-xs mt-2 opacity-75">
                        Charts will display here once Chart.js is installed
                      </p>
                    </div>
                  </div>
                )}

                {/* Health Tab */}
                {activeTab === 'health' && healthHistory.length > 0 && (
                  <div className="space-y-6">
                    <div className={`p-4 rounded-lg ${darkMode ? 'bg-gray-700' : 'bg-gray-50'}`}>
                      <h3 className="font-semibold mb-3">Health Check Summary (24h)</h3>
                      <div className="grid grid-cols-3 gap-4">
                        <div>
                          <p className={`text-sm ${darkMode ? 'text-gray-400' : 'text-gray-600'}`}>Uptime</p>
                          <p className="text-2xl font-bold text-green-500">
                            {((healthHistory.filter(h => h.status === 'healthy').length / healthHistory.length) * 100).toFixed(1)}%
                          </p>
                        </div>
                        <div>
                          <p className={`text-sm ${darkMode ? 'text-gray-400' : 'text-gray-600'}`}>Total Checks</p>
                          <p className="text-2xl font-bold">{healthHistory.length}</p>
                        </div>
                        <div>
                          <p className={`text-sm ${darkMode ? 'text-gray-400' : 'text-gray-600'}`}>Failed</p>
                          <p className="text-2xl font-bold text-red-500">
                            {healthHistory.filter(h => h.status === 'unhealthy').length}
                          </p>
                        </div>
                      </div>
                    </div>

                    <div className={`p-4 rounded-lg ${darkMode ? 'bg-gray-700' : 'bg-gray-50'}`}>
                      <h3 className="font-semibold mb-3">Health Timeline (Hourly)</h3>
                      <div className="flex space-x-1">
                        {healthHistory.map((check, i) => (
                          <div
                            key={i}
                            className={`flex-1 h-8 rounded ${
                              check.status === 'healthy'
                                ? 'bg-green-500'
                                : 'bg-red-500'
                            }`}
                            title={`${new Date(check.timestamp).toLocaleString()}: ${check.status}`}
                          />
                        ))}
                      </div>
                      <div className="flex justify-between mt-2 text-xs opacity-75">
                        <span>24h ago</span>
                        <span>Now</span>
                      </div>
                    </div>
                  </div>
                )}
              </>
            )}
          </div>
        </div>
      </div>
    </>
  );

  return createPortal(modalContent, document.body);
};


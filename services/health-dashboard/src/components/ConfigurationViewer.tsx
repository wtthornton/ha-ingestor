import React, { useState, useEffect } from 'react';
import { Configuration } from '../types';
import { apiService } from '../services/api';

interface ConfigurationViewerProps {
  service: string;
  onEdit?: (config: Configuration) => void;
  onBackup?: (config: Configuration) => void;
  onRestore?: () => void;
}

interface ConfigSection {
  title: string;
  fields: ConfigField[];
}

interface ConfigField {
  key: string;
  value: any;
  type: 'string' | 'number' | 'boolean' | 'object' | 'array';
  sensitive: boolean;
  description?: string;
  required?: boolean;
}

export const ConfigurationViewer: React.FC<ConfigurationViewerProps> = ({
  service,
  onEdit,
  onBackup,
  onRestore,
}) => {
  const [configuration, setConfiguration] = useState<Configuration | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showSensitive, setShowSensitive] = useState(false);
  const [expandedSections, setExpandedSections] = useState<Set<string>>(new Set());

  useEffect(() => {
    fetchConfiguration();
  }, [service]);

  const fetchConfiguration = async () => {
    try {
      setLoading(true);
      setError(null);
      const config = await apiService.getConfiguration(false); // Don't include sensitive data initially
      setConfiguration(config);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch configuration');
    } finally {
      setLoading(false);
    }
  };

  const toggleSensitiveData = async () => {
    try {
      const config = await apiService.getConfiguration(!showSensitive);
      setConfiguration(config);
      setShowSensitive(!showSensitive);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to toggle sensitive data');
    }
  };

  const toggleSection = (sectionTitle: string) => {
    const newExpanded = new Set(expandedSections);
    if (newExpanded.has(sectionTitle)) {
      newExpanded.delete(sectionTitle);
    } else {
      newExpanded.add(sectionTitle);
    }
    setExpandedSections(newExpanded);
  };

  const organizeConfiguration = (config: Configuration): ConfigSection[] => {
    const sections: ConfigSection[] = [];
    const sectionMap = new Map<string, ConfigField[]>();

    Object.entries(config).forEach(([key, value]) => {
      const field: ConfigField = {
        key,
        value,
        type: getValueType(value),
        sensitive: isSensitiveField(key),
        description: getFieldDescription(key),
        required: isRequiredField(key),
      };

      const sectionTitle = getSectionTitle(key);
      if (!sectionMap.has(sectionTitle)) {
        sectionMap.set(sectionTitle, []);
      }
      sectionMap.get(sectionTitle)!.push(field);
    });

    sectionMap.forEach((fields, title) => {
      sections.push({ title, fields });
    });

    return sections;
  };

  const getValueType = (value: any): ConfigField['type'] => {
    if (Array.isArray(value)) return 'array';
    if (typeof value === 'object' && value !== null) return 'object';
    if (typeof value === 'boolean') return 'boolean';
    if (typeof value === 'number') return 'number';
    return 'string';
  };

  const isSensitiveField = (key: string): boolean => {
    const sensitiveKeys = ['password', 'token', 'secret', 'key', 'auth', 'credential'];
    return sensitiveKeys.some(sensitive => key.toLowerCase().includes(sensitive));
  };

  const getFieldDescription = (key: string): string => {
    const descriptions: Record<string, string> = {
      'home_assistant_url': 'URL of the Home Assistant instance',
      'home_assistant_token': 'Authentication token for Home Assistant API',
      'influxdb_url': 'URL of the InfluxDB instance',
      'influxdb_token': 'Authentication token for InfluxDB',
      'influxdb_org': 'InfluxDB organization name',
      'influxdb_bucket': 'InfluxDB bucket name for storing events',
      'weather_api_key': 'API key for weather service',
      'log_level': 'Logging level (DEBUG, INFO, WARNING, ERROR)',
      'max_workers': 'Maximum number of worker threads',
      'batch_size': 'Number of events to process in each batch',
      'batch_timeout': 'Timeout for batch processing in seconds',
    };
    return descriptions[key] || '';
  };

  const isRequiredField = (key: string): boolean => {
    const requiredFields = ['home_assistant_url', 'home_assistant_token', 'influxdb_url', 'influxdb_token'];
    return requiredFields.includes(key);
  };

  const getSectionTitle = (key: string): string => {
    if (key.startsWith('home_assistant')) return 'Home Assistant';
    if (key.startsWith('influxdb')) return 'InfluxDB';
    if (key.startsWith('weather')) return 'Weather Service';
    if (key.startsWith('log')) return 'Logging';
    if (key.includes('batch') || key.includes('worker')) return 'Processing';
    return 'General';
  };

  const formatValue = (field: ConfigField): string => {
    if (field.sensitive && !showSensitive) {
      return '••••••••';
    }

    switch (field.type) {
      case 'object':
        return JSON.stringify(field.value, null, 2);
      case 'array':
        return JSON.stringify(field.value, null, 2);
      case 'boolean':
        return field.value ? 'true' : 'false';
      default:
        return String(field.value);
    }
  };

  const getValueColor = (field: ConfigField): string => {
    if (field.sensitive && !showSensitive) return 'text-gray-500';
    if (field.type === 'boolean') return field.value ? 'text-green-600' : 'text-red-600';
    if (field.type === 'number') return 'text-blue-600';
    return 'text-gray-900';
  };

  if (loading) {
    return (
      <div className="bg-white rounded-lg shadow-md p-6">
        <div className="animate-pulse">
          <div className="h-4 bg-gray-200 rounded w-1/4 mb-4"></div>
          <div className="space-y-3">
            <div className="h-3 bg-gray-200 rounded w-3/4"></div>
            <div className="h-3 bg-gray-200 rounded w-1/2"></div>
            <div className="h-3 bg-gray-200 rounded w-2/3"></div>
          </div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-white rounded-lg shadow-md p-6">
        <div className="text-center">
          <div className="text-red-600 mb-4">
            <svg className="mx-auto h-12 w-12" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L3.732 16.5c-.77.833.192 2.5 1.732 2.5z" />
            </svg>
          </div>
          <h3 className="text-lg font-medium text-gray-900 mb-2">Configuration Error</h3>
          <p className="text-gray-600 mb-4">{error}</p>
          <button
            onClick={fetchConfiguration}
            className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            Retry
          </button>
        </div>
      </div>
    );
  }

  if (!configuration) {
    return (
      <div className="bg-white rounded-lg shadow-md p-6">
        <div className="text-center text-gray-500">No configuration available</div>
      </div>
    );
  }

  const sections = organizeConfiguration(configuration);

  return (
    <div className="bg-white rounded-lg shadow-md p-6">
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-xl font-semibold text-gray-900">
          Configuration: {service}
        </h2>
        <div className="flex space-x-2">
          <button
            onClick={toggleSensitiveData}
            className={`px-3 py-1 rounded text-sm font-medium ${
              showSensitive
                ? 'bg-red-100 text-red-800 hover:bg-red-200'
                : 'bg-gray-100 text-gray-800 hover:bg-gray-200'
            }`}
          >
            {showSensitive ? 'Hide Sensitive' : 'Show Sensitive'}
          </button>
          <button
            onClick={() => onEdit?.(configuration)}
            className="px-3 py-1 bg-blue-100 text-blue-800 rounded text-sm font-medium hover:bg-blue-200"
          >
            Edit
          </button>
          <button
            onClick={() => onBackup?.(configuration)}
            className="px-3 py-1 bg-green-100 text-green-800 rounded text-sm font-medium hover:bg-green-200"
          >
            Backup
          </button>
          <button
            onClick={onRestore}
            className="px-3 py-1 bg-yellow-100 text-yellow-800 rounded text-sm font-medium hover:bg-yellow-200"
          >
            Restore
          </button>
        </div>
      </div>

      <div className="space-y-4">
        {sections.map((section) => (
          <div key={section.title} className="border border-gray-200 rounded-lg">
            <button
              onClick={() => toggleSection(section.title)}
              className="w-full px-4 py-3 text-left bg-gray-50 hover:bg-gray-100 rounded-t-lg flex items-center justify-between"
            >
              <h3 className="font-medium text-gray-900">{section.title}</h3>
              <svg
                className={`w-5 h-5 transform transition-transform ${
                  expandedSections.has(section.title) ? 'rotate-180' : ''
                }`}
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
              >
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
              </svg>
            </button>
            
            {expandedSections.has(section.title) && (
              <div className="p-4 space-y-3">
                {section.fields.map((field) => (
                  <div key={field.key} className="grid grid-cols-1 md:grid-cols-3 gap-4">
                    <div className="md:col-span-1">
                      <div className="flex items-center space-x-2">
                        <label className="font-medium text-gray-700">
                          {field.key}
                        </label>
                        {field.required && (
                          <span className="text-red-500 text-sm">*</span>
                        )}
                        {field.sensitive && (
                          <span className="text-orange-500 text-sm">🔒</span>
                        )}
                      </div>
                      {field.description && (
                        <p className="text-sm text-gray-500 mt-1">{field.description}</p>
                      )}
                    </div>
                    <div className="md:col-span-2">
                      <div className={`p-3 bg-gray-50 rounded border ${getValueColor(field)}`}>
                        <pre className="whitespace-pre-wrap text-sm font-mono">
                          {formatValue(field)}
                        </pre>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        ))}
      </div>

      <div className="mt-6 pt-4 border-t border-gray-200">
        <div className="text-xs text-gray-500">
          Last updated: {new Date().toLocaleString()}
        </div>
      </div>
    </div>
  );
};

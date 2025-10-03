import React, { useState, useEffect } from 'react';
import { Configuration, ConfigUpdate } from '../types';
import { apiService } from '../services/api';

interface ConfigurationEditorProps {
  service: string;
  configuration: Configuration;
  onSave?: (updates: ConfigUpdate[]) => void;
  onCancel?: () => void;
}

interface EditableField {
  key: string;
  value: any;
  originalValue: any;
  type: 'string' | 'number' | 'boolean' | 'object' | 'array';
  sensitive: boolean;
  description?: string;
  required?: boolean;
  error?: string;
}

export const ConfigurationEditor: React.FC<ConfigurationEditorProps> = ({
  service,
  configuration,
  onSave,
  onCancel,
}) => {
  const [fields, setFields] = useState<EditableField[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [hasChanges, setHasChanges] = useState(false);

  useEffect(() => {
    initializeFields();
  }, [configuration]);

  const initializeFields = () => {
    const editableFields: EditableField[] = Object.entries(configuration).map(([key, value]) => ({
      key,
      value,
      originalValue: value,
      type: getValueType(value),
      sensitive: isSensitiveField(key),
      description: getFieldDescription(key),
      required: isRequiredField(key),
    }));
    setFields(editableFields);
  };

  const getValueType = (value: any): EditableField['type'] => {
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

  const updateField = (key: string, value: any) => {
    setFields(prev => prev.map(field => {
      if (field.key === key) {
        const updatedField = { ...field, value };
        const hasChanged = JSON.stringify(updatedField.value) !== JSON.stringify(field.originalValue);
        setHasChanges(hasChanged);
        return updatedField;
      }
      return field;
    }));
  };

  const validateField = (field: EditableField): string | undefined => {
    if (field.required && (!field.value || field.value === '')) {
      return 'This field is required';
    }

    switch (field.type) {
      case 'string':
        if (typeof field.value !== 'string') {
          return 'Value must be a string';
        }
        break;
      case 'number':
        if (isNaN(Number(field.value))) {
          return 'Value must be a number';
        }
        break;
      case 'boolean':
        if (typeof field.value !== 'boolean') {
          return 'Value must be true or false';
        }
        break;
      case 'object':
        try {
          if (typeof field.value === 'string') {
            JSON.parse(field.value);
          }
        } catch {
          return 'Value must be valid JSON';
        }
        break;
      case 'array':
        try {
          if (typeof field.value === 'string') {
            JSON.parse(field.value);
          }
        } catch {
          return 'Value must be valid JSON array';
        }
        break;
    }

    return undefined;
  };

  const validateAllFields = (): boolean => {
    let isValid = true;
    setFields(prev => prev.map(field => {
      const error = validateField(field);
      if (error) isValid = false;
      return { ...field, error };
    }));
    return isValid;
  };

  const handleSave = async () => {
    if (!validateAllFields()) {
      setError('Please fix validation errors before saving');
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const updates: ConfigUpdate[] = fields
        .filter(field => JSON.stringify(field.value) !== JSON.stringify(field.originalValue))
        .map(field => ({
          key: field.key,
          value: field.value,
          reason: `Updated via configuration interface`,
        }));

      if (updates.length === 0) {
        setError('No changes to save');
        setLoading(false);
        return;
      }

      await apiService.updateConfiguration(service, updates);
      onSave?.(updates);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to save configuration');
    } finally {
      setLoading(false);
    }
  };

  const handleCancel = () => {
    initializeFields();
    setHasChanges(false);
    setError(null);
    onCancel?.();
  };

  const renderFieldInput = (field: EditableField) => {
    const commonProps = {
      value: field.value,
      onChange: (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement>) => {
        let newValue: any = e.target.value;
        
        if (field.type === 'number') {
          newValue = Number(e.target.value);
        } else if (field.type === 'boolean') {
          newValue = (e.target as HTMLInputElement).checked;
        } else if (field.type === 'object' || field.type === 'array') {
          try {
            newValue = JSON.parse(e.target.value);
          } catch {
            newValue = e.target.value; // Keep as string for now, validation will catch it
          }
        }
        
        updateField(field.key, newValue);
      },
      className: `w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 ${
        field.error ? 'border-red-300' : 'border-gray-300'
      }`,
    };

    switch (field.type) {
      case 'boolean':
        return (
          <div className="flex items-center">
            <input
              type="checkbox"
              checked={field.value}
              onChange={(e) => updateField(field.key, e.target.checked)}
              className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
            />
            <span className="ml-2 text-sm text-gray-700">
              {field.value ? 'Enabled' : 'Disabled'}
            </span>
          </div>
        );

      case 'number':
        return (
          <input
            type="number"
            {...commonProps}
            placeholder="Enter number"
          />
        );

      case 'object':
      case 'array':
        return (
          <textarea
            {...commonProps}
            rows={4}
            placeholder="Enter JSON"
            value={typeof field.value === 'string' ? field.value : JSON.stringify(field.value, null, 2)}
          />
        );

      default:
        return (
          <input
            type={field.sensitive ? 'password' : 'text'}
            {...commonProps}
            placeholder={`Enter ${field.key}`}
          />
        );
    }
  };

  return (
    <div className="bg-white rounded-lg shadow-md p-6">
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-xl font-semibold text-gray-900">
          Edit Configuration: {service}
        </h2>
        <div className="flex space-x-2">
          <button
            onClick={handleCancel}
            className="px-4 py-2 border border-gray-300 text-gray-700 rounded hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            Cancel
          </button>
          <button
            onClick={handleSave}
            disabled={loading || !hasChanges}
            className={`px-4 py-2 rounded text-white focus:outline-none focus:ring-2 focus:ring-blue-500 ${
              loading || !hasChanges
                ? 'bg-gray-400 cursor-not-allowed'
                : 'bg-blue-600 hover:bg-blue-700'
            }`}
          >
            {loading ? 'Saving...' : 'Save Changes'}
          </button>
        </div>
      </div>

      {error && (
        <div className="mb-6 bg-red-50 border border-red-200 rounded-md p-4">
          <div className="flex">
            <div className="flex-shrink-0">
              <svg className="h-5 w-5 text-red-400" viewBox="0 0 20 20" fill="currentColor">
                <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
              </svg>
            </div>
            <div className="ml-3">
              <h3 className="text-sm font-medium text-red-800">Error</h3>
              <div className="mt-2 text-sm text-red-700">{error}</div>
            </div>
          </div>
        </div>
      )}

      <div className="space-y-6">
        {fields.map((field) => (
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
              {renderFieldInput(field)}
              {field.error && (
                <p className="mt-1 text-sm text-red-600">{field.error}</p>
              )}
            </div>
          </div>
        ))}
      </div>

      {hasChanges && (
        <div className="mt-6 pt-4 border-t border-gray-200">
          <div className="text-sm text-gray-600">
            You have unsaved changes. Click "Save Changes" to apply them.
          </div>
        </div>
      )}
    </div>
  );
};

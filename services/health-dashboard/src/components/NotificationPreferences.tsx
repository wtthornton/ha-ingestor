import React, { useState } from 'react';
import { NotificationPreferences, NotificationCategory } from '../types/notification';
import { useNotificationPreferences } from '../contexts/NotificationContext';

interface NotificationPreferencesProps {
  className?: string;
}

export const NotificationPreferences: React.FC<NotificationPreferencesProps> = ({ className = '' }) => {
  const { preferences, updatePreferences } = useNotificationPreferences();
  const [localPreferences, setLocalPreferences] = useState(preferences);

  const handleSave = () => {
    updatePreferences(localPreferences);
  };

  const handleReset = () => {
    setLocalPreferences(preferences);
  };

  const handleCategoryChange = (category: NotificationCategory, enabled: boolean) => {
    setLocalPreferences(prev => ({
      ...prev,
      categories: {
        ...prev.categories,
        [category]: enabled,
      },
    }));
  };

  const handleSeverityChange = (severity: keyof NotificationPreferences['severity'], enabled: boolean) => {
    setLocalPreferences(prev => ({
      ...prev,
      severity: {
        ...prev.severity,
        [severity]: enabled,
      },
    }));
  };

  const handleThresholdChange = (key: keyof NotificationPreferences['thresholds'], value: number) => {
    setLocalPreferences(prev => ({
      ...prev,
      thresholds: {
        ...prev.thresholds,
        [key]: value,
      },
    }));
  };

  const handleChannelChange = (channel: keyof NotificationPreferences['channels'], enabled: boolean) => {
    setLocalPreferences(prev => ({
      ...prev,
      channels: {
        ...prev.channels,
        [channel]: enabled,
      },
    }));
  };

  const categoryLabels: Record<NotificationCategory, string> = {
    system_status: 'System Status',
    error_alert: 'Error Alerts',
    performance: 'Performance',
    maintenance: 'Maintenance',
    user_action: 'User Actions',
    data_update: 'Data Updates',
  };

  const severityLabels: Record<keyof NotificationPreferences['severity'], string> = {
    info: 'Info',
    warning: 'Warning',
    error: 'Error',
    success: 'Success',
  };

  const channelLabels: Record<keyof NotificationPreferences['channels'], string> = {
    toast: 'Toast Notifications',
    center: 'Notification Center',
    sound: 'Sound Alerts',
  };

  return (
    <div className={`bg-white rounded-lg shadow-md p-6 ${className}`}>
      <h3 className="text-lg font-semibold text-gray-900 mb-6">Notification Preferences</h3>

      <div className="space-y-6">
        {/* Global Enable/Disable */}
        <div className="flex items-center justify-between">
          <div>
            <h4 className="text-sm font-medium text-gray-900">Enable Notifications</h4>
            <p className="text-sm text-gray-500">Turn all notifications on or off</p>
          </div>
          <label className="relative inline-flex items-center cursor-pointer">
            <input
              type="checkbox"
              checked={localPreferences.enabled}
              onChange={(e) => setLocalPreferences(prev => ({ ...prev, enabled: e.target.checked }))}
              className="sr-only peer"
            />
            <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-blue-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-blue-600"></div>
          </label>
        </div>

        {/* Categories */}
        <div>
          <h4 className="text-sm font-medium text-gray-900 mb-3">Notification Categories</h4>
          <div className="grid grid-cols-2 gap-3">
            {Object.entries(categoryLabels).map(([category, label]) => (
              <label key={category} className="flex items-center">
                <input
                  type="checkbox"
                  checked={localPreferences.categories[category as NotificationCategory]}
                  onChange={(e) => handleCategoryChange(category as NotificationCategory, e.target.checked)}
                  className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                />
                <span className="ml-2 text-sm text-gray-700">{label}</span>
              </label>
            ))}
          </div>
        </div>

        {/* Severity Levels */}
        <div>
          <h4 className="text-sm font-medium text-gray-900 mb-3">Severity Levels</h4>
          <div className="grid grid-cols-2 gap-3">
            {Object.entries(severityLabels).map(([severity, label]) => (
              <label key={severity} className="flex items-center">
                <input
                  type="checkbox"
                  checked={localPreferences.severity[severity as keyof NotificationPreferences['severity']]}
                  onChange={(e) => handleSeverityChange(severity as keyof NotificationPreferences['severity'], e.target.checked)}
                  className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                />
                <span className="ml-2 text-sm text-gray-700">{label}</span>
              </label>
            ))}
          </div>
        </div>

        {/* Channels */}
        <div>
          <h4 className="text-sm font-medium text-gray-900 mb-3">Notification Channels</h4>
          <div className="space-y-3">
            {Object.entries(channelLabels).map(([channel, label]) => (
              <label key={channel} className="flex items-center">
                <input
                  type="checkbox"
                  checked={localPreferences.channels[channel as keyof NotificationPreferences['channels']]}
                  onChange={(e) => handleChannelChange(channel as keyof NotificationPreferences['channels'], e.target.checked)}
                  className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                />
                <span className="ml-2 text-sm text-gray-700">{label}</span>
              </label>
            ))}
          </div>
        </div>

        {/* Thresholds */}
        <div>
          <h4 className="text-sm font-medium text-gray-900 mb-3">Thresholds</h4>
          <div className="space-y-4">
            <div>
              <label className="block text-sm text-gray-700 mb-1">
                Maximum Notifications
              </label>
              <input
                type="number"
                min="10"
                max="200"
                value={localPreferences.thresholds.maxNotifications}
                onChange={(e) => handleThresholdChange('maxNotifications', parseInt(e.target.value))}
                className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              />
            </div>
            
            <div>
              <label className="block text-sm text-gray-700 mb-1">
                Auto-dismiss Delay (seconds)
              </label>
              <input
                type="number"
                min="1"
                max="60"
                value={localPreferences.thresholds.autoDismissDelay / 1000}
                onChange={(e) => handleThresholdChange('autoDismissDelay', parseInt(e.target.value) * 1000)}
                className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              />
            </div>
            
            <div>
              <label className="block text-sm text-gray-700 mb-1">
                Persistent Threshold (minimum severity for persistent notifications)
              </label>
              <select
                value={localPreferences.thresholds.persistentThreshold}
                onChange={(e) => handleThresholdChange('persistentThreshold', parseInt(e.target.value))}
                className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              >
                <option value={0}>Info</option>
                <option value={1}>Success</option>
                <option value={2}>Warning</option>
                <option value={3}>Error</option>
              </select>
            </div>
          </div>
        </div>

        {/* Actions */}
        <div className="flex justify-end space-x-3 pt-4 border-t border-gray-200">
          <button
            onClick={handleReset}
            className="px-4 py-2 text-sm font-medium text-gray-700 bg-gray-100 border border-gray-300 rounded-md hover:bg-gray-200 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2"
          >
            Reset
          </button>
          <button
            onClick={handleSave}
            className="px-4 py-2 text-sm font-medium text-white bg-blue-600 border border-transparent rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2"
          >
            Save Preferences
          </button>
        </div>
      </div>
    </div>
  );
};

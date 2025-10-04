import React from 'react';
import { Navigation } from './Navigation';
import { ThemeToggle } from './ThemeToggle';
import { NotificationPreferences } from './NotificationPreferences';
import { useThemeAware } from '../contexts/ThemeContext';

const Settings: React.FC = () => {
  const { isDark } = useThemeAware();

  return (
    <div className="min-h-screen bg-design-background transition-colors duration-design-normal">
      <Navigation />
      
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="space-y-6">
          {/* Page Header */}
          <div className="bg-design-surface rounded-design-lg shadow-design-md p-6">
            <h1 className="text-2xl font-bold text-design-text mb-2">Settings</h1>
            <p className="text-design-text-secondary">
              Configure your dashboard preferences and system settings.
            </p>
          </div>

          {/* Theme Settings */}
          <div className="bg-design-surface rounded-design-lg shadow-design-md p-6">
            <h2 className="text-lg font-semibold text-design-text mb-4">Appearance</h2>
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-design-text-secondary mb-2">
                  Theme
                </label>
                <ThemeToggle variant="select" />
                <p className="mt-1 text-xs text-design-text-tertiary">
                  Choose between light, dark, or system theme
                </p>
              </div>
            </div>
          </div>

          {/* Notification Settings */}
          <NotificationPreferences />

          {/* System Information */}
          <div className="bg-design-surface rounded-design-lg shadow-design-md p-6">
            <h2 className="text-lg font-semibold text-design-text mb-4">System Information</h2>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-design-text-secondary mb-1">
                  Current Theme
                </label>
                <p className="text-sm text-design-text capitalize">{isDark ? 'Dark' : 'Light'}</p>
              </div>
              <div>
                <label className="block text-sm font-medium text-design-text-secondary mb-1">
                  Version
                </label>
                <p className="text-sm text-design-text">1.0.0</p>
              </div>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
};

export default Settings;

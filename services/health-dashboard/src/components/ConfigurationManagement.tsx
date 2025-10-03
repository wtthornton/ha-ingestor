import React, { useState } from 'react';
import { Configuration, ConfigUpdate } from '../types';
import { ConfigurationViewer } from './ConfigurationViewer';
import { ConfigurationEditor } from './ConfigurationEditor';
import { ConfigurationBackup } from './ConfigurationBackup';

type ViewMode = 'view' | 'edit' | 'backup';

export const ConfigurationManagement: React.FC = () => {
  const [currentService, setCurrentService] = useState<string>('websocket-ingestion');
  const [viewMode, setViewMode] = useState<ViewMode>('view');
  const [currentConfiguration, setCurrentConfiguration] = useState<Configuration | null>(null);

  const services = [
    { id: 'websocket-ingestion', name: 'WebSocket Ingestion', description: 'Home Assistant WebSocket connection service' },
    { id: 'enrichment-pipeline', name: 'Enrichment Pipeline', description: 'Data normalization and enrichment service' },
    { id: 'weather-api', name: 'Weather API', description: 'Weather data enrichment service' },
    { id: 'admin-api', name: 'Admin API', description: 'Administrative REST API service' },
  ];

  const handleEditConfiguration = (config: Configuration) => {
    setCurrentConfiguration(config);
    setViewMode('edit');
  };

  const handleBackupConfiguration = (config: Configuration) => {
    setCurrentConfiguration(config);
    setViewMode('backup');
  };

  const handleRestoreConfiguration = () => {
    setViewMode('backup');
  };

  const handleSaveConfiguration = (updates: ConfigUpdate[]) => {
    console.log('Configuration saved:', updates);
    setViewMode('view');
    setCurrentConfiguration(null);
  };

  const handleCancelEdit = () => {
    setViewMode('view');
    setCurrentConfiguration(null);
  };

  const handleBackupComplete = () => {
    console.log('Backup completed');
  };

  const handleRestoreComplete = () => {
    console.log('Restore completed');
    setViewMode('view');
    setCurrentConfiguration(null);
  };

  const renderContent = () => {
    switch (viewMode) {
      case 'edit':
        return currentConfiguration ? (
          <ConfigurationEditor
            service={currentService}
            configuration={currentConfiguration}
            onSave={handleSaveConfiguration}
            onCancel={handleCancelEdit}
          />
        ) : null;

      case 'backup':
        return (
          <ConfigurationBackup
            service={currentService}
            onBackupComplete={handleBackupComplete}
            onRestoreComplete={handleRestoreComplete}
          />
        );

      default:
        return (
          <ConfigurationViewer
            service={currentService}
            onEdit={handleEditConfiguration}
            onBackup={handleBackupConfiguration}
            onRestore={handleRestoreConfiguration}
          />
        );
    }
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white shadow-sm border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center py-4">
            <div>
              <h1 className="text-2xl font-bold text-gray-900">Configuration Management</h1>
              <p className="text-sm text-gray-600">Manage system configuration settings</p>
            </div>
            
            <div className="flex items-center space-x-4">
              {/* View Mode Selector */}
              <div className="flex bg-gray-100 rounded-lg p-1">
                <button
                  onClick={() => setViewMode('view')}
                  className={`px-3 py-1 rounded text-sm font-medium ${
                    viewMode === 'view'
                      ? 'bg-white text-gray-900 shadow-sm'
                      : 'text-gray-600 hover:text-gray-900'
                  }`}
                >
                  View
                </button>
                <button
                  onClick={() => setViewMode('edit')}
                  className={`px-3 py-1 rounded text-sm font-medium ${
                    viewMode === 'edit'
                      ? 'bg-white text-gray-900 shadow-sm'
                      : 'text-gray-600 hover:text-gray-900'
                  }`}
                >
                  Edit
                </button>
                <button
                  onClick={() => setViewMode('backup')}
                  className={`px-3 py-1 rounded text-sm font-medium ${
                    viewMode === 'backup'
                      ? 'bg-white text-gray-900 shadow-sm'
                      : 'text-gray-600 hover:text-gray-900'
                  }`}
                >
                  Backup
                </button>
              </div>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
          {/* Service Sidebar */}
          <div className="lg:col-span-1">
            <div className="bg-white rounded-lg shadow-md p-6">
              <h2 className="text-lg font-semibold text-gray-900 mb-4">Services</h2>
              <div className="space-y-2">
                {services.map((service) => (
                  <button
                    key={service.id}
                    onClick={() => setCurrentService(service.id)}
                    className={`w-full text-left p-3 rounded-lg transition-colors ${
                      currentService === service.id
                        ? 'bg-blue-50 border border-blue-200 text-blue-900'
                        : 'hover:bg-gray-50 text-gray-700'
                    }`}
                  >
                    <div className="font-medium">{service.name}</div>
                    <div className="text-sm text-gray-500">{service.description}</div>
                  </button>
                ))}
              </div>
            </div>

            {/* Quick Actions */}
            <div className="bg-white rounded-lg shadow-md p-6 mt-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">Quick Actions</h3>
              <div className="space-y-2">
                <button
                  onClick={() => setViewMode('view')}
                  className="w-full text-left p-2 text-sm text-gray-700 hover:bg-gray-50 rounded"
                >
                  📋 View Configuration
                </button>
                <button
                  onClick={() => setViewMode('edit')}
                  className="w-full text-left p-2 text-sm text-gray-700 hover:bg-gray-50 rounded"
                >
                  ✏️ Edit Configuration
                </button>
                <button
                  onClick={() => setViewMode('backup')}
                  className="w-full text-left p-2 text-sm text-gray-700 hover:bg-gray-50 rounded"
                >
                  💾 Backup & Restore
                </button>
              </div>
            </div>
          </div>

          {/* Main Content Area */}
          <div className="lg:col-span-3">
            {renderContent()}
          </div>
        </div>
      </main>
    </div>
  );
};

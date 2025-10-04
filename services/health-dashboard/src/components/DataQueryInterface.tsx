import React, { useState } from 'react';
import { EventData, EventFilter } from '../types';
import { EventBrowser } from './EventBrowser';
import { DataVisualization } from './DataVisualization';
import { SavedQueries } from './SavedQueries';
import { ExportDialog } from './ExportDialog';
import { ExportHistory } from './ExportHistory';
import { ExportResult } from '../utils/exportUtils';
import { useThemeAware } from '../contexts/ThemeContext';

export const DataQueryInterface: React.FC = () => {
  const [currentEvents, setCurrentEvents] = useState<EventData[]>([]);
  const [currentFilters, setCurrentFilters] = useState<EventFilter>({});
  const [activeTab, setActiveTab] = useState<'browser' | 'visualization' | 'queries' | 'history'>('browser');
  const [showExportDialog, setShowExportDialog] = useState(false);
  const { isDark } = useThemeAware();

  const handleEventsUpdate = (events: EventData[]) => {
    setCurrentEvents(events);
  };

  const handleFiltersUpdate = (filters: EventFilter) => {
    setCurrentFilters(filters);
  };

  const handleLoadQuery = (filters: EventFilter) => {
    setCurrentFilters(filters);
    setActiveTab('browser');
  };

  const handleExportData = (events: EventData[], format: 'csv' | 'json') => {
    setCurrentEvents(events);
    setShowExportDialog(true);
  };

  const handleExportComplete = (result: ExportResult) => {
    if (result.success) {
      console.log('Export completed successfully:', result.filename);
    } else {
      console.error('Export failed:', result.error);
    }
  };

  const exportToCSV = (events: EventData[]) => {
    if (events.length === 0) return;

    const headers = ['ID', 'Timestamp', 'Entity ID', 'Event Type', 'State', 'Attributes'];
    const rows = events.map(event => [
      event.id,
      event.timestamp,
      event.entity_id,
      event.event_type,
      event.new_state?.state || '',
      JSON.stringify(event.attributes || {}),
    ]);

    const csvContent = [
      headers.join(','),
      ...rows.map(row => row.map(cell => `"${cell}"`).join(','))
    ].join('\n');

    const blob = new Blob([csvContent], { type: 'text/csv' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `events-export-${new Date().toISOString().split('T')[0]}.csv`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
  };

  const exportToJSON = (events: EventData[]) => {
    const jsonContent = JSON.stringify(events, null, 2);
    const blob = new Blob([jsonContent], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `events-export-${new Date().toISOString().split('T')[0]}.json`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
  };

  const renderTabContent = () => {
    switch (activeTab) {
      case 'browser':
        return (
          <EventBrowser
            onExport={handleExportData}
            onEventsUpdate={handleEventsUpdate}
            onFiltersUpdate={handleFiltersUpdate}
          />
        );
      case 'visualization':
        return (
          <DataVisualization
            events={currentEvents}
          />
        );
      case 'queries':
        return (
          <SavedQueries
            onLoadQuery={handleLoadQuery}
          />
        );
      case 'history':
        return (
          <ExportHistory />
        );
      default:
        return null;
    }
  };

  return (
    <div className="min-h-screen bg-design-background transition-colors duration-design-normal">
      {/* Header */}
      <header className="bg-design-surface shadow-design-sm border-b border-design-border">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center py-4">
            <div>
              <h1 className="text-2xl font-bold text-design-text">Data Query Interface</h1>
              <p className="text-sm text-design-text-secondary">Search, analyze, and export Home Assistant events</p>
            </div>
            
            <div className="flex items-center space-x-4">
              {/* Quick Stats */}
              <div className="text-sm text-design-text-secondary">
                {currentEvents.length} events loaded
              </div>
              <button
                onClick={() => setShowExportDialog(true)}
                className="px-3 py-1 bg-design-primary text-design-text-inverse rounded-design-md text-sm
                  hover:bg-design-primary-hover transition-colors duration-design-fast shadow-design-sm"
              >
                Export Data
              </button>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Tab Navigation */}
        <div className="mb-6">
          <div className="border-b border-design-border">
            <nav className="-mb-px flex space-x-8">
              <button
                onClick={() => setActiveTab('browser')}
                className={`py-2 px-1 border-b-2 font-medium text-sm transition-colors duration-design-fast ${
                  activeTab === 'browser'
                    ? 'border-design-primary text-design-primary'
                    : 'border-transparent text-design-text-secondary hover:text-design-text hover:border-design-border-hover'
                }`}
              >
                <svg className="w-5 h-5 inline mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
                </svg>
                Event Browser
              </button>
              
              <button
                onClick={() => setActiveTab('visualization')}
                className={`py-2 px-1 border-b-2 font-medium text-sm transition-colors duration-design-fast ${
                  activeTab === 'visualization'
                    ? 'border-design-primary text-design-primary'
                    : 'border-transparent text-design-text-secondary hover:text-design-text hover:border-design-border-hover'
                }`}
              >
                <svg className="w-5 h-5 inline mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
                </svg>
                Data Visualization
              </button>
              
              <button
                onClick={() => setActiveTab('queries')}
                className={`py-2 px-1 border-b-2 font-medium text-sm transition-colors duration-design-fast ${
                  activeTab === 'queries'
                    ? 'border-design-primary text-design-primary'
                    : 'border-transparent text-design-text-secondary hover:text-design-text hover:border-design-border-hover'
                }`}
              >
                <svg className="w-5 h-5 inline mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 5a2 2 0 012-2h10a2 2 0 012 2v16l-7-3.5L5 21V5z" />
                </svg>
                Saved Queries
              </button>
              
              <button
                onClick={() => setActiveTab('history')}
                className={`py-2 px-1 border-b-2 font-medium text-sm transition-colors duration-design-fast ${
                  activeTab === 'history'
                    ? 'border-design-primary text-design-primary'
                    : 'border-transparent text-design-text-secondary hover:text-design-text hover:border-design-border-hover'
                }`}
              >
                <svg className="w-5 h-5 inline mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
                Export History
              </button>
            </nav>
          </div>
        </div>

        {/* Tab Content */}
        <div className="space-y-6">
          {renderTabContent()}
        </div>

        {/* Help Section */}
        <div className="mt-8 bg-design-background-secondary border border-design-border rounded-design-lg p-6">
          <h3 className="text-lg font-medium text-design-text mb-2">Getting Started</h3>
          <div className="text-sm text-design-text-secondary space-y-2">
            <p><strong>Event Browser:</strong> Use filters to find specific events, then export your results in multiple formats.</p>
            <p><strong>Data Visualization:</strong> Create charts and graphs to analyze trends in your Home Assistant data.</p>
            <p><strong>Saved Queries:</strong> Save frequently used filter combinations for quick access later.</p>
            <p><strong>Export History:</strong> View and manage your previous data exports.</p>
          </div>
        </div>
      </main>

      {/* Export Dialog */}
      <ExportDialog
        isOpen={showExportDialog}
        onClose={() => setShowExportDialog(false)}
        events={currentEvents}
        onExportComplete={handleExportComplete}
      />
    </div>
  );
};

import React, { useState, useEffect } from 'react';
import { XMarkIcon, DocumentArrowDownIcon, ChartBarIcon } from '@heroicons/react/24/outline';
import { 
  ExportOptions, 
  ExportResult, 
  HistoricalAnalysisOptions,
  exportEventsToCSV,
  exportEventsToJSON,
  exportEventsToExcel,
  performHistoricalAnalysis,
  ExportHistoryManager
} from '../utils/exportUtils';
import { EventData } from '../types';
import { useThemeAware } from '../contexts/ThemeContext';

interface ExportDialogProps {
  isOpen: boolean;
  onClose: () => void;
  events: EventData[];
  onExportComplete?: (result: ExportResult) => void;
}

export const ExportDialog: React.FC<ExportDialogProps> = ({
  isOpen,
  onClose,
  events,
  onExportComplete,
}) => {
  const { isDark } = useThemeAware();
  const [isExporting, setIsExporting] = useState(false);
  const [progress, setProgress] = useState(0);
  const [exportOptions, setExportOptions] = useState<ExportOptions>({
    filename: `events-export-${new Date().toISOString().split('T')[0]}`,
    title: 'Events Export',
    includeMetadata: true,
    dateRange: {
      start: new Date(Date.now() - 7 * 24 * 60 * 60 * 1000), // 7 days ago
      end: new Date(),
    },
  });
  const [selectedFormat, setSelectedFormat] = useState<'csv' | 'json' | 'pdf' | 'excel'>('csv');
  const [showAdvanced, setShowAdvanced] = useState(false);
  const [historicalAnalysis, setHistoricalAnalysis] = useState<HistoricalAnalysisOptions>({
    timeRange: {
      start: new Date(Date.now() - 30 * 24 * 60 * 60 * 1000), // 30 days ago
      end: new Date(),
    },
    aggregation: 'day',
    metrics: ['event_count'],
    groupBy: ['entity_id'],
  });

  useEffect(() => {
    if (isOpen) {
      setProgress(0);
      setIsExporting(false);
    }
  }, [isOpen]);

  const handleExport = async () => {
    if (events.length === 0) {
      onExportComplete?.({
        success: false,
        error: 'No events to export',
      });
      return;
    }

    setIsExporting(true);
    setProgress(0);

    try {
      // Simulate progress updates
      const progressInterval = setInterval(() => {
        setProgress(prev => {
          if (prev >= 90) {
            clearInterval(progressInterval);
            return prev;
          }
          return prev + 10;
        });
      }, 100);

      let result: ExportResult;

      // Filter events based on date range
      const filteredEvents = events.filter(event => {
        const eventTime = new Date(event.timestamp);
        return eventTime >= exportOptions.dateRange!.start && 
               eventTime <= exportOptions.dateRange!.end;
      });

      // Perform export based on selected format
      switch (selectedFormat) {
        case 'csv':
          result = exportEventsToCSV(filteredEvents, exportOptions);
          break;
        case 'json':
          result = exportEventsToJSON(filteredEvents, exportOptions);
          break;
        case 'excel':
          result = exportEventsToExcel(filteredEvents, exportOptions);
          break;
        case 'pdf':
          // For PDF, we'll create a summary report
          result = {
            success: false,
            error: 'PDF export requires chart element. Use chart export instead.',
          };
          break;
        default:
          result = {
            success: false,
            error: 'Unsupported export format',
          };
      }

      clearInterval(progressInterval);
      setProgress(100);

      // Add to export history
      if (result.success) {
        ExportHistoryManager.addToHistory({
          filename: result.filename || exportOptions.filename!,
          format: selectedFormat,
          size: filteredEvents.length,
          status: 'completed',
          options: exportOptions,
        });
      }

      onExportComplete?.(result);
      
      // Close dialog after a short delay
      setTimeout(() => {
        setIsExporting(false);
        onClose();
      }, 1000);

    } catch (error) {
      setIsExporting(false);
      onExportComplete?.({
        success: false,
        error: error instanceof Error ? error.message : 'Export failed',
      });
    }
  };

  const handleHistoricalAnalysis = () => {
    const analysisData = performHistoricalAnalysis(events, historicalAnalysis);
    
    // Export the analysis as CSV
    const result = exportEventsToCSV(events, {
      ...exportOptions,
      filename: `historical-analysis-${new Date().toISOString().split('T')[0]}.csv`,
      title: 'Historical Analysis',
    });

    if (result.success) {
      ExportHistoryManager.addToHistory({
        filename: result.filename!,
        format: 'csv',
        size: events.length,
        status: 'completed',
        options: exportOptions,
      });
    }

    onExportComplete?.(result);
  };

  const formatFileSize = (bytes: number): string => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 overflow-hidden">
      {/* Backdrop */}
      <div 
        className="absolute inset-0 bg-black bg-opacity-25"
        onClick={onClose}
      />
      
      {/* Dialog */}
      <div className="absolute inset-0 flex items-center justify-center p-4">
        <div className={`
          relative bg-design-surface rounded-design-lg shadow-design-xl max-w-2xl w-full
          border border-design-border
          ${isDark ? 'bg-design-background-secondary' : 'bg-white'}
        `}>
          {/* Header */}
          <div className="flex items-center justify-between p-6 border-b border-design-border">
            <div className="flex items-center space-x-3">
              <DocumentArrowDownIcon className="h-6 w-6 text-design-primary" />
              <h2 className="text-xl font-semibold text-design-text">Export Data</h2>
            </div>
            <button
              onClick={onClose}
              className="text-design-text-secondary hover:text-design-text transition-colors duration-design-fast"
            >
              <XMarkIcon className="h-6 w-6" />
            </button>
          </div>

          {/* Content */}
          <div className="p-6 space-y-6">
            {/* Export Summary */}
            <div className="bg-design-background-secondary rounded-design-md p-4">
              <h3 className="text-sm font-medium text-design-text mb-2">Export Summary</h3>
              <div className="grid grid-cols-2 gap-4 text-sm text-design-text-secondary">
                <div>
                  <span className="font-medium">Total Events:</span> {events.length.toLocaleString()}
                </div>
                <div>
                  <span className="font-medium">Date Range:</span> {exportOptions.dateRange?.start.toLocaleDateString()} - {exportOptions.dateRange?.end.toLocaleDateString()}
                </div>
                <div>
                  <span className="font-medium">Estimated Size:</span> {formatFileSize(events.length * 200)}
                </div>
                <div>
                  <span className="font-medium">Format:</span> {selectedFormat.toUpperCase()}
                </div>
              </div>
            </div>

            {/* Format Selection */}
            <div>
              <label className="block text-sm font-medium text-design-text mb-3">
                Export Format
              </label>
              <div className="grid grid-cols-2 gap-3">
                {[
                  { value: 'csv', label: 'CSV', desc: 'Spreadsheet compatible' },
                  { value: 'json', label: 'JSON', desc: 'Structured data' },
                  { value: 'excel', label: 'Excel', desc: 'Advanced spreadsheet' },
                  { value: 'pdf', label: 'PDF', desc: 'Formatted report' },
                ].map((format) => (
                  <label
                    key={format.value}
                    className={`
                      flex items-center p-3 rounded-design-md border cursor-pointer transition-colors duration-design-fast
                      ${selectedFormat === format.value
                        ? 'border-design-primary bg-design-primary-light text-design-primary-dark'
                        : 'border-design-border hover:border-design-border-hover hover:bg-design-surface-hover'
                      }
                    `}
                  >
                    <input
                      type="radio"
                      name="format"
                      value={format.value}
                      checked={selectedFormat === format.value}
                      onChange={(e) => setSelectedFormat(e.target.value as any)}
                      className="sr-only"
                    />
                    <div>
                      <div className="font-medium">{format.label}</div>
                      <div className="text-xs opacity-75">{format.desc}</div>
                    </div>
                  </label>
                ))}
              </div>
            </div>

            {/* Export Options */}
            <div>
              <label className="block text-sm font-medium text-design-text mb-3">
                Export Options
              </label>
              <div className="space-y-3">
                <div>
                  <label className="block text-sm text-design-text-secondary mb-1">
                    Filename
                  </label>
                  <input
                    type="text"
                    value={exportOptions.filename}
                    onChange={(e) => setExportOptions(prev => ({ ...prev, filename: e.target.value }))}
                    className="w-full px-3 py-2 border border-design-border rounded-design-md text-sm
                      bg-design-surface text-design-text
                      focus:outline-none focus:ring-2 focus:ring-design-border-focus focus:border-design-border-focus"
                  />
                </div>
                
                <div>
                  <label className="block text-sm text-design-text-secondary mb-1">
                    Title
                  </label>
                  <input
                    type="text"
                    value={exportOptions.title}
                    onChange={(e) => setExportOptions(prev => ({ ...prev, title: e.target.value }))}
                    className="w-full px-3 py-2 border border-design-border rounded-design-md text-sm
                      bg-design-surface text-design-text
                      focus:outline-none focus:ring-2 focus:ring-design-border-focus focus:border-design-border-focus"
                  />
                </div>

                <label className="flex items-center">
                  <input
                    type="checkbox"
                    checked={exportOptions.includeMetadata}
                    onChange={(e) => setExportOptions(prev => ({ ...prev, includeMetadata: e.target.checked }))}
                    className="h-4 w-4 text-design-primary focus:ring-design-border-focus border-design-border rounded"
                  />
                  <span className="ml-2 text-sm text-design-text-secondary">
                    Include metadata (export info, timestamps, etc.)
                  </span>
                </label>
              </div>
            </div>

            {/* Advanced Options */}
            <div>
              <button
                onClick={() => setShowAdvanced(!showAdvanced)}
                className="flex items-center text-sm text-design-primary hover:text-design-primary-hover transition-colors duration-design-fast"
              >
                <ChartBarIcon className="h-4 w-4 mr-1" />
                {showAdvanced ? 'Hide' : 'Show'} Historical Analysis Options
              </button>
              
              {showAdvanced && (
                <div className="mt-3 p-4 bg-design-background-secondary rounded-design-md space-y-3">
                  <div>
                    <label className="block text-sm text-design-text-secondary mb-1">
                      Aggregation Period
                    </label>
                    <select
                      value={historicalAnalysis.aggregation}
                      onChange={(e) => setHistoricalAnalysis(prev => ({ 
                        ...prev, 
                        aggregation: e.target.value as any 
                      }))}
                      className="w-full px-3 py-2 border border-design-border rounded-design-md text-sm
                        bg-design-surface text-design-text
                        focus:outline-none focus:ring-2 focus:ring-design-border-focus focus:border-design-border-focus"
                    >
                      <option value="hour">Hour</option>
                      <option value="day">Day</option>
                      <option value="week">Week</option>
                      <option value="month">Month</option>
                    </select>
                  </div>
                  
                  <div>
                    <label className="block text-sm text-design-text-secondary mb-1">
                      Analysis Time Range
                    </label>
                    <div className="grid grid-cols-2 gap-2">
                      <input
                        type="date"
                        value={historicalAnalysis.timeRange.start.toISOString().split('T')[0]}
                        onChange={(e) => setHistoricalAnalysis(prev => ({
                          ...prev,
                          timeRange: { ...prev.timeRange, start: new Date(e.target.value) }
                        }))}
                        className="px-3 py-2 border border-design-border rounded-design-md text-sm
                          bg-design-surface text-design-text
                          focus:outline-none focus:ring-2 focus:ring-design-border-focus focus:border-design-border-focus"
                      />
                      <input
                        type="date"
                        value={historicalAnalysis.timeRange.end.toISOString().split('T')[0]}
                        onChange={(e) => setHistoricalAnalysis(prev => ({
                          ...prev,
                          timeRange: { ...prev.timeRange, end: new Date(e.target.value) }
                        }))}
                        className="px-3 py-2 border border-design-border rounded-design-md text-sm
                          bg-design-surface text-design-text
                          focus:outline-none focus:ring-2 focus:ring-design-border-focus focus:border-design-border-focus"
                      />
                    </div>
                  </div>
                </div>
              )}
            </div>

            {/* Progress Bar */}
            {isExporting && (
              <div className="space-y-2">
                <div className="flex justify-between text-sm text-design-text-secondary">
                  <span>Exporting...</span>
                  <span>{progress}%</span>
                </div>
                <div className="w-full bg-design-border rounded-full h-2">
                  <div
                    className="bg-design-primary h-2 rounded-full transition-all duration-design-normal"
                    style={{ width: `${progress}%` }}
                  />
                </div>
              </div>
            )}
          </div>

          {/* Footer */}
          <div className="flex items-center justify-end space-x-3 p-6 border-t border-design-border">
            <button
              onClick={onClose}
              disabled={isExporting}
              className="px-4 py-2 text-sm font-medium text-design-text-secondary
                hover:text-design-text transition-colors duration-design-fast
                disabled:opacity-50 disabled:cursor-not-allowed"
            >
              Cancel
            </button>
            
            {showAdvanced && (
              <button
                onClick={handleHistoricalAnalysis}
                disabled={isExporting}
                className="px-4 py-2 text-sm font-medium text-design-text
                  bg-design-secondary hover:bg-design-secondary-hover
                  rounded-design-md transition-colors duration-design-fast
                  disabled:opacity-50 disabled:cursor-not-allowed"
              >
                Export Analysis
              </button>
            )}
            
            <button
              onClick={handleExport}
              disabled={isExporting || events.length === 0}
              className="px-4 py-2 text-sm font-medium text-design-text-inverse
                bg-design-primary hover:bg-design-primary-hover
                rounded-design-md transition-colors duration-design-fast
                disabled:opacity-50 disabled:cursor-not-allowed
                shadow-design-sm hover:shadow-design-md"
            >
              {isExporting ? 'Exporting...' : 'Export Data'}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

import React, { useState, useEffect } from 'react';
import { 
  DocumentArrowDownIcon, 
  TrashIcon, 
  EyeIcon,
  CalendarIcon,
  DocumentTextIcon
} from '@heroicons/react/24/outline';
import { ExportHistoryManager, ExportHistoryItem } from '../utils/exportUtils';
import { useThemeAware } from '../contexts/ThemeContext';

interface ExportHistoryProps {
  className?: string;
}

export const ExportHistory: React.FC<ExportHistoryProps> = ({ className = '' }) => {
  const { isDark } = useThemeAware();
  const [history, setHistory] = useState<ExportHistoryItem[]>([]);
  const [selectedItems, setSelectedItems] = useState<Set<string>>(new Set());

  useEffect(() => {
    setHistory(ExportHistoryManager.getHistory());
  }, []);

  const handleRemoveItem = (id: string) => {
    ExportHistoryManager.removeFromHistory(id);
    setHistory(ExportHistoryManager.getHistory());
    setSelectedItems(prev => {
      const newSet = new Set(prev);
      newSet.delete(id);
      return newSet;
    });
  };

  const handleRemoveSelected = () => {
    selectedItems.forEach(id => {
      ExportHistoryManager.removeFromHistory(id);
    });
    setHistory(ExportHistoryManager.getHistory());
    setSelectedItems(new Set());
  };

  const handleClearAll = () => {
    ExportHistoryManager.clearHistory();
    setHistory([]);
    setSelectedItems(new Set());
  };

  const handleSelectItem = (id: string) => {
    setSelectedItems(prev => {
      const newSet = new Set(prev);
      if (newSet.has(id)) {
        newSet.delete(id);
      } else {
        newSet.add(id);
      }
      return newSet;
    });
  };

  const handleSelectAll = () => {
    if (selectedItems.size === history.length) {
      setSelectedItems(new Set());
    } else {
      setSelectedItems(new Set(history.map(item => item.id)));
    }
  };

  const formatFileSize = (bytes: number): string => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  const getStatusColor = (status: ExportHistoryItem['status']) => {
    switch (status) {
      case 'completed':
        return 'text-design-success bg-design-success-light';
      case 'failed':
        return 'text-design-error bg-design-error-light';
      case 'processing':
        return 'text-design-warning bg-design-warning-light';
      default:
        return 'text-design-text-secondary bg-design-background-tertiary';
    }
  };

  const getFormatIcon = (format: string) => {
    switch (format.toLowerCase()) {
      case 'csv':
        return <DocumentTextIcon className="h-4 w-4" />;
      case 'json':
        return <DocumentTextIcon className="h-4 w-4" />;
      case 'pdf':
        return <DocumentArrowDownIcon className="h-4 w-4" />;
      case 'excel':
        return <DocumentTextIcon className="h-4 w-4" />;
      default:
        return <DocumentArrowDownIcon className="h-4 w-4" />;
    }
  };

  if (history.length === 0) {
    return (
      <div className={`bg-design-surface rounded-design-lg shadow-design-md p-6 ${className}`}>
        <div className="text-center">
          <DocumentArrowDownIcon className="mx-auto h-12 w-12 text-design-text-tertiary" />
          <h3 className="mt-2 text-sm font-medium text-design-text">No export history</h3>
          <p className="mt-1 text-sm text-design-text-secondary">
            Your export history will appear here once you start exporting data.
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className={`bg-design-surface rounded-design-lg shadow-design-md ${className}`}>
      {/* Header */}
      <div className="flex items-center justify-between p-6 border-b border-design-border">
        <div className="flex items-center space-x-3">
          <DocumentArrowDownIcon className="h-6 w-6 text-design-primary" />
          <h2 className="text-xl font-semibold text-design-text">Export History</h2>
          <span className="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium bg-design-primary-light text-design-primary-dark">
            {history.length}
          </span>
        </div>
        
        <div className="flex items-center space-x-2">
          {selectedItems.size > 0 && (
            <button
              onClick={handleRemoveSelected}
              className="px-3 py-1 text-sm text-design-error hover:text-design-error-hover
                hover:bg-design-error-light rounded-design-md transition-colors duration-design-fast"
            >
              Remove Selected ({selectedItems.size})
            </button>
          )}
          <button
            onClick={handleClearAll}
            className="px-3 py-1 text-sm text-design-text-secondary hover:text-design-text
              hover:bg-design-surface-hover rounded-design-md transition-colors duration-design-fast"
          >
            Clear All
          </button>
        </div>
      </div>

      {/* History List */}
      <div className="divide-y divide-design-border">
        {/* Select All Header */}
        <div className="px-6 py-3 bg-design-background-secondary">
          <label className="flex items-center">
            <input
              type="checkbox"
              checked={selectedItems.size === history.length && history.length > 0}
              onChange={handleSelectAll}
              className="h-4 w-4 text-design-primary focus:ring-design-border-focus border-design-border rounded"
            />
            <span className="ml-2 text-sm text-design-text-secondary">
              Select All ({history.length} items)
            </span>
          </label>
        </div>

        {history.map((item) => (
          <div
            key={item.id}
            className={`p-4 hover:bg-design-surface-hover transition-colors duration-design-fast ${
              selectedItems.has(item.id) ? 'bg-design-primary-light' : ''
            }`}
          >
            <div className="flex items-center space-x-3">
              <input
                type="checkbox"
                checked={selectedItems.has(item.id)}
                onChange={() => handleSelectItem(item.id)}
                className="h-4 w-4 text-design-primary focus:ring-design-border-focus border-design-border rounded"
              />
              
              <div className="flex-shrink-0">
                <div className="flex items-center justify-center w-8 h-8 bg-design-background-secondary rounded-design-md">
                  {getFormatIcon(item.format)}
                </div>
              </div>
              
              <div className="flex-1 min-w-0">
                <div className="flex items-center justify-between">
                  <p className="text-sm font-medium text-design-text truncate">
                    {item.filename}
                  </p>
                  <div className="flex items-center space-x-2">
                    <span className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium ${getStatusColor(item.status)}`}>
                      {item.status}
                    </span>
                    <button
                      onClick={() => handleRemoveItem(item.id)}
                      className="text-design-text-tertiary hover:text-design-error transition-colors duration-design-fast"
                    >
                      <TrashIcon className="h-4 w-4" />
                    </button>
                  </div>
                </div>
                
                <div className="mt-1 flex items-center space-x-4 text-xs text-design-text-secondary">
                  <div className="flex items-center space-x-1">
                    <CalendarIcon className="h-3 w-3" />
                    <span>{item.timestamp.toLocaleString()}</span>
                  </div>
                  <div className="flex items-center space-x-1">
                    <DocumentArrowDownIcon className="h-3 w-3" />
                    <span>{item.format.toUpperCase()}</span>
                  </div>
                  <div className="flex items-center space-x-1">
                    <span>{formatFileSize(item.size * 200)}</span>
                  </div>
                </div>
                
                {item.options.title && (
                  <p className="mt-1 text-xs text-design-text-tertiary">
                    {item.options.title}
                  </p>
                )}
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* Footer */}
      <div className="px-6 py-3 bg-design-background-secondary border-t border-design-border">
        <div className="flex items-center justify-between text-xs text-design-text-secondary">
          <span>
            Showing {history.length} export{history.length !== 1 ? 's' : ''}
          </span>
          <span>
            Total size: {formatFileSize(history.reduce((sum, item) => sum + item.size * 200, 0))}
          </span>
        </div>
      </div>
    </div>
  );
};

import React, { useState, useEffect } from 'react';
import { EventFilter } from '../types';

interface SavedQuery {
  id: string;
  name: string;
  description?: string;
  filters: EventFilter;
  createdAt: string;
  lastUsed?: string;
  useCount: number;
}

interface SavedQueriesProps {
  onLoadQuery?: (filters: EventFilter) => void;
  onSaveQuery?: (query: Omit<SavedQuery, 'id' | 'createdAt' | 'useCount'>) => void;
}

export const SavedQueries: React.FC<SavedQueriesProps> = ({ onLoadQuery, onSaveQuery }) => {
  const [queries, setQueries] = useState<SavedQuery[]>([]);
  const [showSaveDialog, setShowSaveDialog] = useState(false);
  const [newQueryName, setNewQueryName] = useState('');
  const [newQueryDescription, setNewQueryDescription] = useState('');
  const [currentFilters, setCurrentFilters] = useState<EventFilter>({});

  useEffect(() => {
    loadSavedQueries();
  }, []);

  const loadSavedQueries = () => {
    try {
      const saved = localStorage.getItem('saved_queries');
      if (saved) {
        setQueries(JSON.parse(saved));
      }
    } catch (error) {
      console.error('Failed to load saved queries:', error);
    }
  };

  const saveQueriesToStorage = (updatedQueries: SavedQuery[]) => {
    try {
      localStorage.setItem('saved_queries', JSON.stringify(updatedQueries));
      setQueries(updatedQueries);
    } catch (error) {
      console.error('Failed to save queries:', error);
    }
  };

  const handleSaveQuery = () => {
    if (!newQueryName.trim()) return;

    const newQuery: SavedQuery = {
      id: Date.now().toString(),
      name: newQueryName.trim(),
      description: newQueryDescription.trim() || undefined,
      filters: currentFilters,
      createdAt: new Date().toISOString(),
      useCount: 0,
    };

    const updatedQueries = [...queries, newQuery];
    saveQueriesToStorage(updatedQueries);
    
    setNewQueryName('');
    setNewQueryDescription('');
    setShowSaveDialog(false);
    onSaveQuery?.(newQuery);
  };

  const handleLoadQuery = (query: SavedQuery) => {
    const updatedQueries = queries.map(q => 
      q.id === query.id 
        ? { ...q, lastUsed: new Date().toISOString(), useCount: q.useCount + 1 }
        : q
    );
    saveQueriesToStorage(updatedQueries);
    onLoadQuery?.(query.filters);
  };

  const handleDeleteQuery = (queryId: string) => {
    if (window.confirm('Are you sure you want to delete this saved query?')) {
      const updatedQueries = queries.filter(q => q.id !== queryId);
      saveQueriesToStorage(updatedQueries);
    }
  };

  const handleExportQueries = () => {
    const dataStr = JSON.stringify(queries, null, 2);
    const dataBlob = new Blob([dataStr], { type: 'application/json' });
    const url = URL.createObjectURL(dataBlob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `saved-queries-${new Date().toISOString().split('T')[0]}.json`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
  };

  const handleImportQueries = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;

    const reader = new FileReader();
    reader.onload = (e) => {
      try {
        const importedQueries = JSON.parse(e.target?.result as string);
        if (Array.isArray(importedQueries)) {
          const updatedQueries = [...queries, ...importedQueries];
          saveQueriesToStorage(updatedQueries);
        }
      } catch (error) {
        alert('Failed to import queries. Please check the file format.');
      }
    };
    reader.readAsText(file);
    
    // Reset file input
    event.target.value = '';
  };

  const formatDate = (dateString: string): string => {
    return new Date(dateString).toLocaleDateString();
  };

  const getFilterSummary = (filters: EventFilter): string => {
    const parts: string[] = [];
    if (filters.entity_id) parts.push(`Entity: ${filters.entity_id}`);
    if (filters.event_type) parts.push(`Type: ${filters.event_type}`);
    if (filters.start_time) parts.push(`From: ${new Date(filters.start_time).toLocaleDateString()}`);
    if (filters.end_time) parts.push(`To: ${new Date(filters.end_time).toLocaleDateString()}`);
    if (filters.limit) parts.push(`Limit: ${filters.limit}`);
    return parts.join(', ') || 'No filters';
  };

  return (
    <div className="bg-white rounded-lg shadow-md p-6">
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-xl font-semibold text-gray-900">Saved Queries</h2>
        <div className="flex items-center space-x-2">
          <button
            onClick={() => setShowSaveDialog(true)}
            className="px-3 py-1 bg-blue-100 text-blue-800 rounded text-sm font-medium hover:bg-blue-200"
          >
            Save Current Query
          </button>
          <button
            onClick={handleExportQueries}
            className="px-3 py-1 bg-green-100 text-green-800 rounded text-sm font-medium hover:bg-green-200"
          >
            Export
          </button>
          <label className="px-3 py-1 bg-purple-100 text-purple-800 rounded text-sm font-medium hover:bg-purple-200 cursor-pointer">
            Import
            <input
              type="file"
              accept=".json"
              onChange={handleImportQueries}
              className="hidden"
            />
          </label>
        </div>
      </div>

      {/* Save Query Dialog */}
      {showSaveDialog && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 w-96 max-w-full mx-4">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">Save Query</h3>
            
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Query Name *
                </label>
                <input
                  type="text"
                  value={newQueryName}
                  onChange={(e) => setNewQueryName(e.target.value)}
                  placeholder="Enter query name"
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Description
                </label>
                <textarea
                  value={newQueryDescription}
                  onChange={(e) => setNewQueryDescription(e.target.value)}
                  placeholder="Enter query description (optional)"
                  rows={3}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>
              
              <div className="text-sm text-gray-600">
                <strong>Current filters:</strong> {getFilterSummary(currentFilters)}
              </div>
            </div>
            
            <div className="flex justify-end space-x-2 mt-6">
              <button
                onClick={() => setShowSaveDialog(false)}
                className="px-4 py-2 border border-gray-300 text-gray-700 rounded hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                Cancel
              </button>
              <button
                onClick={handleSaveQuery}
                disabled={!newQueryName.trim()}
                className={`px-4 py-2 rounded text-white focus:outline-none focus:ring-2 focus:ring-blue-500 ${
                  !newQueryName.trim()
                    ? 'bg-gray-400 cursor-not-allowed'
                    : 'bg-blue-600 hover:bg-blue-700'
                }`}
              >
                Save Query
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Queries List */}
      {queries.length === 0 ? (
        <div className="text-center py-8 text-gray-500">
          <svg className="mx-auto h-12 w-12 text-gray-400 mb-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
          </svg>
          <p>No saved queries yet</p>
          <p className="text-sm">Save your first query to get started</p>
        </div>
      ) : (
        <div className="space-y-3">
          {queries.map((query) => (
            <div key={query.id} className="border border-gray-200 rounded-lg p-4 hover:bg-gray-50">
              <div className="flex items-start justify-between">
                <div className="flex-1">
                  <div className="flex items-center space-x-2 mb-2">
                    <h3 className="font-medium text-gray-900">{query.name}</h3>
                    <span className="text-xs bg-gray-100 text-gray-600 px-2 py-1 rounded">
                      Used {query.useCount} times
                    </span>
                  </div>
                  
                  {query.description && (
                    <p className="text-sm text-gray-600 mb-2">{query.description}</p>
                  )}
                  
                  <div className="text-sm text-gray-500 mb-2">
                    {getFilterSummary(query.filters)}
                  </div>
                  
                  <div className="text-xs text-gray-400">
                    Created: {formatDate(query.createdAt)}
                    {query.lastUsed && (
                      <span className="ml-2">Last used: {formatDate(query.lastUsed)}</span>
                    )}
                  </div>
                </div>
                
                <div className="flex items-center space-x-2">
                  <button
                    onClick={() => handleLoadQuery(query)}
                    className="px-3 py-1 bg-blue-100 text-blue-800 rounded text-sm font-medium hover:bg-blue-200"
                  >
                    Load
                  </button>
                  <button
                    onClick={() => handleDeleteQuery(query.id)}
                    className="px-3 py-1 bg-red-100 text-red-800 rounded text-sm font-medium hover:bg-red-200"
                  >
                    Delete
                  </button>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      <div className="mt-6 pt-4 border-t border-gray-200">
        <div className="text-xs text-gray-500">
          <strong>Note:</strong> Saved queries are stored locally in your browser. Export them to share or backup.
        </div>
      </div>
    </div>
  );
};

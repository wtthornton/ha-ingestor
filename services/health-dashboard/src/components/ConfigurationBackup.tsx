import React, { useState, useRef } from 'react';
// import { Configuration } from '../types';
import { apiService } from '../services/api';

interface ConfigurationBackupProps {
  service: string;
  onBackupComplete?: () => void;
  onRestoreComplete?: () => void;
}

interface BackupHistory {
  id: string;
  timestamp: string;
  size: number;
  description?: string;
}

export const ConfigurationBackup: React.FC<ConfigurationBackupProps> = ({
  service,
  onBackupComplete,
  onRestoreComplete,
}) => {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [backupHistory, setBackupHistory] = useState<BackupHistory[]>([]);
  const [showHistory, setShowHistory] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const downloadBackup = async () => {
    setLoading(true);
    setError(null);
    setSuccess(null);

    try {
      const backupData = await apiService.backupConfiguration(service);
      
      // Create downloadable file
      const blob = new Blob([JSON.stringify(backupData, null, 2)], {
        type: 'application/json',
      });
      
      const url = URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = `${service}-config-backup-${new Date().toISOString().split('T')[0]}.json`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      URL.revokeObjectURL(url);

      setSuccess('Configuration backup downloaded successfully');
      onBackupComplete?.();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to create backup');
    } finally {
      setLoading(false);
    }
  };

  const handleFileUpload = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;

    setLoading(true);
    setError(null);
    setSuccess(null);

    try {
      const text = await file.text();
      const backupData = JSON.parse(text);
      
      await apiService.restoreConfiguration(service, backupData);
      
      setSuccess('Configuration restored successfully');
      onRestoreComplete?.();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to restore configuration');
    } finally {
      setLoading(false);
      // Reset file input
      if (fileInputRef.current) {
        fileInputRef.current.value = '';
      }
    }
  };

  const fetchBackupHistory = async () => {
    try {
      const history = await apiService.getConfigHistory(service, 10);
      setBackupHistory(history);
      setShowHistory(true);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch backup history');
    }
  };

  const formatFileSize = (bytes: number): string => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  const formatTimestamp = (timestamp: string): string => {
    return new Date(timestamp).toLocaleString();
  };

  return (
    <div className="bg-white rounded-lg shadow-md p-6">
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-xl font-semibold text-gray-900">
          Configuration Backup & Restore
        </h2>
        <button
          onClick={fetchBackupHistory}
          className="px-3 py-1 bg-gray-100 text-gray-800 rounded text-sm font-medium hover:bg-gray-200"
        >
          View History
        </button>
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

      {success && (
        <div className="mb-6 bg-green-50 border border-green-200 rounded-md p-4">
          <div className="flex">
            <div className="flex-shrink-0">
              <svg className="h-5 w-5 text-green-400" viewBox="0 0 20 20" fill="currentColor">
                <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
              </svg>
            </div>
            <div className="ml-3">
              <h3 className="text-sm font-medium text-green-800">Success</h3>
              <div className="mt-2 text-sm text-green-700">{success}</div>
            </div>
          </div>
        </div>
      )}

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Backup Section */}
        <div className="border border-gray-200 rounded-lg p-4">
          <div className="flex items-center mb-4">
            <svg className="h-6 w-6 text-blue-600 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
            </svg>
            <h3 className="text-lg font-medium text-gray-900">Create Backup</h3>
          </div>
          
          <p className="text-sm text-gray-600 mb-4">
            Download a complete backup of the current configuration. This includes all settings and can be used to restore the configuration later.
          </p>
          
          <button
            onClick={downloadBackup}
            disabled={loading}
            className={`w-full px-4 py-2 rounded text-white focus:outline-none focus:ring-2 focus:ring-blue-500 ${
              loading
                ? 'bg-gray-400 cursor-not-allowed'
                : 'bg-blue-600 hover:bg-blue-700'
            }`}
          >
            {loading ? 'Creating Backup...' : 'Download Backup'}
          </button>
        </div>

        {/* Restore Section */}
        <div className="border border-gray-200 rounded-lg p-4">
          <div className="flex items-center mb-4">
            <svg className="h-6 w-6 text-green-600 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M9 19l3 3m0 0l3-3m-3 3V10" />
            </svg>
            <h3 className="text-lg font-medium text-gray-900">Restore Backup</h3>
          </div>
          
          <p className="text-sm text-gray-600 mb-4">
            Upload a previously created backup file to restore the configuration. This will overwrite the current settings.
          </p>
          
          <input
            ref={fileInputRef}
            type="file"
            accept=".json"
            onChange={handleFileUpload}
            className="hidden"
          />
          
          <button
            onClick={() => fileInputRef.current?.click()}
            disabled={loading}
            className={`w-full px-4 py-2 rounded text-white focus:outline-none focus:ring-2 focus:ring-green-500 ${
              loading
                ? 'bg-gray-400 cursor-not-allowed'
                : 'bg-green-600 hover:bg-green-700'
            }`}
          >
            {loading ? 'Restoring...' : 'Upload & Restore'}
          </button>
        </div>
      </div>

      {/* Backup History */}
      {showHistory && (
        <div className="mt-6 pt-6 border-t border-gray-200">
          <h3 className="text-lg font-medium text-gray-900 mb-4">Backup History</h3>
          
          {backupHistory.length === 0 ? (
            <div className="text-center py-8 text-gray-500">
              No backup history available
            </div>
          ) : (
            <div className="space-y-3">
              {backupHistory.map((backup) => (
                <div key={backup.id} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                  <div className="flex items-center space-x-3">
                    <svg className="h-5 w-5 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                    </svg>
                    <div>
                      <div className="text-sm font-medium text-gray-900">
                        Backup #{backup.id.slice(-8)}
                      </div>
                      <div className="text-xs text-gray-500">
                        {formatTimestamp(backup.timestamp)}
                      </div>
                    </div>
                  </div>
                  <div className="text-sm text-gray-500">
                    {formatFileSize(backup.size)}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      <div className="mt-6 pt-4 border-t border-gray-200">
        <div className="text-xs text-gray-500">
          <strong>Note:</strong> Backups contain sensitive information. Store them securely and do not share them with unauthorized parties.
        </div>
      </div>
    </div>
  );
};

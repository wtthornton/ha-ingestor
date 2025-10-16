/**
 * AI Automation Tab
 * Epic AI1 Story 13: Display AI-generated automation suggestions
 */

import React, { useState, useEffect } from 'react';
import { aiApi } from '../../services/api';
import type { TabProps } from './types';

interface Suggestion {
  id: number;
  title: string;
  description: string;
  automation_yaml: string;
  status: 'pending' | 'approved' | 'deployed' | 'rejected';
  confidence: number;
  category?: string;
  priority?: string;
  created_at: string;
}

interface ScheduleInfo {
  schedule: string;
  next_run: string | null;
  is_running: boolean;
  recent_jobs: Array<{
    start_time: string;
    status: string;
    events_count?: number;
    patterns_detected?: number;
    suggestions_generated?: number;
    duration_seconds?: number;
    openai_cost_usd?: number;
    error?: string;
  }>;
}

export const AIAutomationTab: React.FC<TabProps> = ({ darkMode }) => {
  const [suggestions, setSuggestions] = useState<Suggestion[]>([]);
  const [scheduleInfo, setScheduleInfo] = useState<ScheduleInfo | null>(null);
  const [loading, setLoading] = useState(true);
  const [triggering, setTriggering] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [selectedStatus, setSelectedStatus] = useState<string>('pending');
  const [expandedYaml, setExpandedYaml] = useState<number | null>(null);

  const loadData = async () => {
    try {
      setLoading(true);
      setError(null);
      
      // Load suggestions and schedule info
      const [suggestionsData, scheduleData] = await Promise.all([
        aiApi.listSuggestions(selectedStatus, 50),
        aiApi.getScheduleInfo()
      ]);
      
      setSuggestions(suggestionsData.data || suggestionsData || []);
      setScheduleInfo(scheduleData);
    } catch (err) {
      console.error('Failed to load AI automation data:', err);
      setError(err instanceof Error ? err.message : 'Failed to load data');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
    // Refresh every 30 seconds
    const interval = setInterval(loadData, 30000);
    return () => clearInterval(interval);
  }, [selectedStatus]);

  const handleTriggerAnalysis = async () => {
    try {
      setTriggering(true);
      await aiApi.triggerManualJob();
      alert('Analysis triggered! This will run in the background. Refresh in 1-2 minutes to see results.');
      setTimeout(loadData, 2000); // Reload after 2 seconds
    } catch (err) {
      alert(`Failed to trigger analysis: ${err instanceof Error ? err.message : 'Unknown error'}`);
    } finally {
      setTriggering(false);
    }
  };

  const getCategoryColor = (category?: string) => {
    const colors = {
      energy: 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200',
      comfort: 'bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200',
      security: 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200',
      convenience: 'bg-purple-100 text-purple-800 dark:bg-purple-900 dark:text-purple-200'
    };
    return colors[category as keyof typeof colors] || 'bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-200';
  };

  const getPriorityColor = (priority?: string) => {
    const colors = {
      high: 'text-red-600 dark:text-red-400',
      medium: 'text-yellow-600 dark:text-yellow-400',
      low: 'text-green-600 dark:text-green-400'
    };
    return colors[priority as keyof typeof colors] || 'text-gray-600 dark:text-gray-400';
  };

  const formatDate = (dateStr: string) => {
    return new Date(dateStr).toLocaleString();
  };

  if (loading && !scheduleInfo) {
    return (
      <div className="p-6">
        <div className="animate-pulse space-y-4">
          <div className="h-32 bg-gray-200 dark:bg-gray-700 rounded"></div>
          <div className="h-64 bg-gray-200 dark:bg-gray-700 rounded"></div>
        </div>
      </div>
    );
  }

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className={`${darkMode ? 'bg-gray-800' : 'bg-white'} rounded-lg shadow p-6`}>
        <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
          <div>
            <h2 className={`text-2xl font-bold ${darkMode ? 'text-white' : 'text-gray-900'}`}>
              🤖 AI Automation Suggestions
            </h2>
            <p className={`text-sm ${darkMode ? 'text-gray-300' : 'text-gray-600'} mt-1`}>
              AI-generated Home Assistant automation recommendations based on your usage patterns
            </p>
          </div>
          
          <div className="flex gap-2">
            <button
              onClick={loadData}
              disabled={loading}
              className={`px-4 py-2 rounded-lg font-medium transition-colors ${
                darkMode
                  ? 'bg-gray-700 text-white hover:bg-gray-600'
                  : 'bg-gray-100 text-gray-900 hover:bg-gray-200'
              } disabled:opacity-50`}
            >
              🔄 Refresh
            </button>
            
            <button
              onClick={handleTriggerAnalysis}
              disabled={triggering || scheduleInfo?.is_running}
              className={`px-4 py-2 rounded-lg font-medium transition-colors ${
                darkMode
                  ? 'bg-blue-600 text-white hover:bg-blue-500'
                  : 'bg-blue-500 text-white hover:bg-blue-600'
              } disabled:opacity-50`}
            >
              {triggering ? '⏳ Running...' : scheduleInfo?.is_running ? '🔄 Analysis Running' : '▶️ Run Analysis'}
            </button>
          </div>
        </div>

        {/* Schedule Info */}
        {scheduleInfo && (
          <div className="mt-4 grid grid-cols-1 md:grid-cols-4 gap-4">
            <div className={`p-3 rounded ${darkMode ? 'bg-gray-700' : 'bg-gray-50'}`}>
              <div className={`text-xs ${darkMode ? 'text-gray-400' : 'text-gray-500'}`}>Schedule</div>
              <div className={`text-sm font-medium ${darkMode ? 'text-white' : 'text-gray-900'}`}>
                Daily at 3:00 AM
              </div>
            </div>
            
            <div className={`p-3 rounded ${darkMode ? 'bg-gray-700' : 'bg-gray-50'}`}>
              <div className={`text-xs ${darkMode ? 'text-gray-400' : 'text-gray-500'}`}>Next Run</div>
              <div className={`text-sm font-medium ${darkMode ? 'text-white' : 'text-gray-900'}`}>
                {scheduleInfo.next_run ? new Date(scheduleInfo.next_run).toLocaleString() : 'N/A'}
              </div>
            </div>
            
            <div className={`p-3 rounded ${darkMode ? 'bg-gray-700' : 'bg-gray-50'}`}>
              <div className={`text-xs ${darkMode ? 'text-gray-400' : 'text-gray-500'}`}>Status</div>
              <div className={`text-sm font-medium ${darkMode ? 'text-white' : 'text-gray-900'}`}>
                {scheduleInfo.is_running ? '🔄 Running' : '✅ Ready'}
              </div>
            </div>
            
            <div className={`p-3 rounded ${darkMode ? 'bg-gray-700' : 'bg-gray-50'}`}>
              <div className={`text-xs ${darkMode ? 'text-gray-400' : 'text-gray-500'}`}>Last Run</div>
              <div className={`text-sm font-medium ${darkMode ? 'text-white' : 'text-gray-900'}`}>
                {scheduleInfo.recent_jobs?.[0] ? (
                  <span className={scheduleInfo.recent_jobs[0].status === 'success' ? 'text-green-600 dark:text-green-400' : 'text-red-600 dark:text-red-400'}>
                    {scheduleInfo.recent_jobs[0].status === 'success' ? '✅ Success' : '❌ Failed'}
                  </span>
                ) : 'No runs yet'}
              </div>
            </div>
          </div>
        )}

        {/* Last Run Details */}
        {scheduleInfo?.recent_jobs?.[0] && (
          <div className={`mt-4 p-4 rounded ${darkMode ? 'bg-gray-700' : 'bg-blue-50'}`}>
            <div className={`text-sm font-medium ${darkMode ? 'text-white' : 'text-gray-900'} mb-2`}>
              Last Analysis Results
            </div>
            <div className="grid grid-cols-2 md:grid-cols-5 gap-3 text-sm">
              <div>
                <span className={darkMode ? 'text-gray-400' : 'text-gray-600'}>Events:</span>
                <span className={`ml-2 font-medium ${darkMode ? 'text-white' : 'text-gray-900'}`}>
                  {scheduleInfo.recent_jobs[0].events_count?.toLocaleString() || 'N/A'}
                </span>
              </div>
              <div>
                <span className={darkMode ? 'text-gray-400' : 'text-gray-600'}>Patterns:</span>
                <span className={`ml-2 font-medium ${darkMode ? 'text-white' : 'text-gray-900'}`}>
                  {scheduleInfo.recent_jobs[0].patterns_detected?.toLocaleString() || 'N/A'}
                </span>
              </div>
              <div>
                <span className={darkMode ? 'text-gray-400' : 'text-gray-600'}>Suggestions:</span>
                <span className={`ml-2 font-medium ${darkMode ? 'text-white' : 'text-gray-900'}`}>
                  {scheduleInfo.recent_jobs[0].suggestions_generated || 'N/A'}
                </span>
              </div>
              <div>
                <span className={darkMode ? 'text-gray-400' : 'text-gray-600'}>Duration:</span>
                <span className={`ml-2 font-medium ${darkMode ? 'text-white' : 'text-gray-900'}`}>
                  {scheduleInfo.recent_jobs[0].duration_seconds?.toFixed(1)}s
                </span>
              </div>
              <div>
                <span className={darkMode ? 'text-gray-400' : 'text-gray-600'}>Cost:</span>
                <span className={`ml-2 font-medium ${darkMode ? 'text-white' : 'text-gray-900'}`}>
                  ${scheduleInfo.recent_jobs[0].openai_cost_usd?.toFixed(4) || '0.0000'}
                </span>
              </div>
            </div>
            {scheduleInfo.recent_jobs[0].error && (
              <div className="mt-2 text-xs text-red-600 dark:text-red-400">
                Error: {scheduleInfo.recent_jobs[0].error}
              </div>
            )}
          </div>
        )}
      </div>

      {/* Error Banner */}
      {error && (
        <div className="bg-red-100 dark:bg-red-900 border border-red-400 dark:border-red-600 text-red-700 dark:text-red-200 px-4 py-3 rounded">
          <strong>Error:</strong> {error}
        </div>
      )}

      {/* Status Filter */}
      <div className="flex gap-2">
        {['pending', 'approved', 'rejected', 'deployed'].map((status) => (
          <button
            key={status}
            onClick={() => setSelectedStatus(status)}
            className={`px-4 py-2 rounded-lg font-medium transition-colors ${
              selectedStatus === status
                ? darkMode
                  ? 'bg-blue-600 text-white'
                  : 'bg-blue-500 text-white'
                : darkMode
                ? 'bg-gray-700 text-gray-300 hover:bg-gray-600'
                : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
            }`}
          >
            {status.charAt(0).toUpperCase() + status.slice(1)} ({suggestions.filter(s => s.status === status).length})
          </button>
        ))}
      </div>

      {/* Suggestions List */}
      <div className="space-y-4">
        {suggestions.length === 0 ? (
          <div className={`${darkMode ? 'bg-gray-800' : 'bg-white'} rounded-lg shadow p-12 text-center`}>
            <div className="text-6xl mb-4">🤖</div>
            <h3 className={`text-xl font-bold mb-2 ${darkMode ? 'text-white' : 'text-gray-900'}`}>
              No {selectedStatus} suggestions
            </h3>
            <p className={`${darkMode ? 'text-gray-400' : 'text-gray-600'}`}>
              {selectedStatus === 'pending' 
                ? 'Run an analysis to generate new automation suggestions based on your usage patterns.'
                : `No ${selectedStatus} suggestions found.`
              }
            </p>
            {selectedStatus === 'pending' && (
              <button
                onClick={handleTriggerAnalysis}
                disabled={triggering}
                className="mt-6 px-6 py-3 bg-blue-500 hover:bg-blue-600 text-white rounded-lg font-medium transition-colors disabled:opacity-50"
              >
                {triggering ? '⏳ Running Analysis...' : '🚀 Run Analysis Now'}
              </button>
            )}
          </div>
        ) : (
          suggestions.map((suggestion) => (
            <div
              key={suggestion.id}
              className={`${darkMode ? 'bg-gray-800 border-gray-700' : 'bg-white border-gray-200'} rounded-lg shadow border p-6`}
            >
              {/* Suggestion Header */}
              <div className="flex justify-between items-start mb-4">
                <div className="flex-1">
                  <h3 className={`text-lg font-bold ${darkMode ? 'text-white' : 'text-gray-900'} mb-2`}>
                    {suggestion.title}
                  </h3>
                  <p className={`text-sm ${darkMode ? 'text-gray-300' : 'text-gray-600'}`}>
                    {suggestion.description}
                  </p>
                </div>
                
                <div className="flex flex-col gap-2 items-end ml-4">
                  {suggestion.category && (
                    <span className={`px-3 py-1 rounded-full text-xs font-medium ${getCategoryColor(suggestion.category)}`}>
                      {suggestion.category}
                    </span>
                  )}
                  {suggestion.priority && (
                    <span className={`text-xs font-medium ${getPriorityColor(suggestion.priority)}`}>
                      {suggestion.priority.toUpperCase()} Priority
                    </span>
                  )}
                </div>
              </div>

              {/* Confidence Bar */}
              <div className="mb-4">
                <div className="flex justify-between text-xs mb-1">
                  <span className={darkMode ? 'text-gray-400' : 'text-gray-600'}>Confidence</span>
                  <span className={`font-medium ${darkMode ? 'text-white' : 'text-gray-900'}`}>
                    {(suggestion.confidence * 100).toFixed(0)}%
                  </span>
                </div>
                <div className={`w-full h-2 rounded-full overflow-hidden ${darkMode ? 'bg-gray-700' : 'bg-gray-200'}`}>
                  <div
                    className={`h-full transition-all ${
                      suggestion.confidence >= 0.9
                        ? 'bg-green-500'
                        : suggestion.confidence >= 0.7
                        ? 'bg-yellow-500'
                        : 'bg-red-500'
                    }`}
                    style={{ width: `${suggestion.confidence * 100}%` }}
                  />
                </div>
              </div>

              {/* YAML Preview */}
              <div className="mb-4">
                <button
                  onClick={() => setExpandedYaml(expandedYaml === suggestion.id ? null : suggestion.id)}
                  className={`w-full text-left px-4 py-2 rounded ${
                    darkMode ? 'bg-gray-700 hover:bg-gray-600' : 'bg-gray-50 hover:bg-gray-100'
                  } transition-colors`}
                >
                  <span className={`text-sm font-medium ${darkMode ? 'text-white' : 'text-gray-900'}`}>
                    {expandedYaml === suggestion.id ? '▼' : '▶'} View Automation YAML
                  </span>
                </button>
                
                {expandedYaml === suggestion.id && (
                  <pre className={`mt-2 p-4 rounded text-xs overflow-x-auto ${
                    darkMode ? 'bg-gray-900 text-gray-300' : 'bg-gray-100 text-gray-800'
                  }`}>
                    {suggestion.automation_yaml}
                  </pre>
                )}
              </div>

              {/* Actions */}
              {suggestion.status === 'pending' && (
                <div className="flex gap-2">
                  <button
                    className="flex-1 px-4 py-2 bg-green-500 hover:bg-green-600 text-white rounded-lg font-medium transition-colors"
                    onClick={() => alert('Approve functionality coming in Story AI1.10!')}
                  >
                    ✅ Approve
                  </button>
                  <button
                    className="flex-1 px-4 py-2 bg-gray-500 hover:bg-gray-600 text-white rounded-lg font-medium transition-colors"
                    onClick={() => alert('Edit functionality coming in Story AI1.10!')}
                  >
                    ✏️ Edit
                  </button>
                  <button
                    className="flex-1 px-4 py-2 bg-red-500 hover:bg-red-600 text-white rounded-lg font-medium transition-colors"
                    onClick={() => alert('Reject functionality coming in Story AI1.10!')}
                  >
                    ❌ Reject
                  </button>
                </div>
              )}

              {/* Metadata */}
              <div className={`mt-4 pt-4 border-t ${darkMode ? 'border-gray-700' : 'border-gray-200'} text-xs ${darkMode ? 'text-gray-400' : 'text-gray-500'}`}>
                Created: {formatDate(suggestion.created_at)}
                {suggestion.status !== 'pending' && ` • Updated: ${formatDate(suggestion.updated_at)}`}
              </div>
            </div>
          ))
        )}
      </div>

      {/* Info Box */}
      <div className={`${darkMode ? 'bg-blue-900' : 'bg-blue-50'} border ${darkMode ? 'border-blue-700' : 'border-blue-200'} rounded-lg p-4`}>
        <div className={`text-sm ${darkMode ? 'text-blue-200' : 'text-blue-800'}`}>
          <strong>💡 How it works:</strong> The AI analyzes your Home Assistant usage patterns (when devices turn on/off, which devices are used together) and generates automation suggestions. 
          Patterns are detected using machine learning, and suggestions are created using OpenAI GPT-4o-mini.
          <br /><br />
          <strong>Cost:</strong> ~$0.0025 per analysis run (~$0.075/month for daily runs)
          <br />
          <strong>Next Features:</strong> Approve/Reject buttons (Story AI1.10), Deploy to HA (Story AI1.11)
        </div>
      </div>
    </div>
  );
};

export default AIAutomationTab;


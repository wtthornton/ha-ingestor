/**
 * Main Dashboard - Suggestion Feed
 * Beautiful card-based interface for viewing and managing AI suggestions
 */

import React, { useEffect, useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { useAppStore } from '../store';
import { SuggestionCard } from '../components/SuggestionCard';
import { SetupWizard } from '../components/SetupWizard';
import { BatchActions } from '../components/BatchActions';
import { SearchBar } from '../components/SearchBar';
import api from '../services/api';

export const Dashboard: React.FC = () => {
  const { 
    suggestions, 
    setSuggestions, 
    selectedStatus, 
    setSelectedStatus,
    scheduleInfo,
    setScheduleInfo,
    darkMode 
  } = useAppStore();

  const [loading, setLoading] = useState(true);
  const [triggering, setTriggering] = useState(false);
  const [error, setError] = useState<string | null>(null);
  
  // UX Enhancements
  const [showWizard, setShowWizard] = useState(!localStorage.getItem('setup_complete'));
  const [selectedSuggestions, setSelectedSuggestions] = useState<Set<number>>(new Set());
  const [searchQuery, setSearchQuery] = useState('');
  const [categoryFilter, setCategoryFilter] = useState<string | null>(null);
  const [minConfidenceFilter, setMinConfidenceFilter] = useState(0);

  const loadData = async () => {
    try {
      setLoading(true);
      setError(null);

      const [suggestionsRes, scheduleRes] = await Promise.all([
        api.getSuggestions(selectedStatus),
        api.getScheduleInfo()
      ]);

      setSuggestions(suggestionsRes.data || []);
      setScheduleInfo(scheduleRes);
    } catch (err) {
      console.error('Failed to load data:', err);
      setError(err instanceof Error ? err.message : 'Failed to load suggestions');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
    const interval = setInterval(loadData, 30000); // Refresh every 30s
    return () => clearInterval(interval);
  }, [selectedStatus]);

  const handleTriggerAnalysis = async () => {
    try {
      setTriggering(true);
      await api.triggerManualJob();
      alert('✅ Analysis started! Refresh in 1-2 minutes to see new suggestions.');
      setTimeout(loadData, 2000);
    } catch (err) {
      alert(`❌ Failed to start analysis: ${err instanceof Error ? err.message : 'Unknown error'}`);
    } finally {
      setTriggering(false);
    }
  };

  const handleApprove = async (id: number) => {
    try {
      await api.approveSuggestion(id);
      alert(`✅ Suggestion approved successfully!`);
      await loadData(); // Refresh data
    } catch (error) {
      alert(`❌ Failed to approve suggestion: ${error}`);
    }
  };

  const handleReject = async (id: number) => {
    const reason = prompt('Why are you rejecting this suggestion? (optional)');
    try {
      await api.rejectSuggestion(id, reason || undefined);
      alert(`✅ Suggestion rejected successfully!`);
      await loadData(); // Refresh data
    } catch (error) {
      alert(`❌ Failed to reject suggestion: ${error}`);
    }
  };

  const handleEdit = async (id: number) => {
    const suggestion = suggestions.find(s => s.id === id);
    if (!suggestion) return;
    
    const newYaml = prompt('Edit YAML automation code:', suggestion.automation_yaml);
    if (newYaml && newYaml !== suggestion.automation_yaml) {
      try {
        await api.updateSuggestion(id, { automation_yaml: newYaml });
        alert(`✅ Suggestion updated successfully!`);
        await loadData(); // Refresh data
      } catch (error) {
        alert(`❌ Failed to update suggestion: ${error}`);
      }
    }
  };

  const handleDeploy = async (id: number) => {
    if (!confirm('Deploy this automation to Home Assistant?')) {
      return;
    }
    
    try {
      const result = await api.deploySuggestion(id);
      alert(`✅ ${result.message}\n\nAutomation ID: ${result.data?.automation_id}`);
      await loadData(); // Refresh data
    } catch (error) {
      alert(`❌ Failed to deploy automation: ${error}`);
    }
  };

  const handleWizardComplete = () => {
    localStorage.setItem('setup_complete', 'true');
    setShowWizard(false);
  };

  const toggleSelection = (id: number) => {
    const newSelection = new Set(selectedSuggestions);
    if (newSelection.has(id)) {
      newSelection.delete(id);
    } else {
      newSelection.add(id);
    }
    setSelectedSuggestions(newSelection);
  };

  const handleBatchApprove = async () => {
    const ids = Array.from(selectedSuggestions);
    if (ids.length === 0) return;
    
    if (!confirm(`Approve ${ids.length} suggestion${ids.length > 1 ? 's' : ''}?`)) {
      return;
    }
    
    try {
      await api.batchApproveSuggestions(ids);
      alert(`✅ Approved ${ids.length} suggestion${ids.length > 1 ? 's' : ''} successfully!`);
      setSelectedSuggestions(new Set());
      await loadData(); // Refresh data
    } catch (error) {
      alert(`❌ Failed to approve suggestions: ${error}`);
    }
  };

  const handleBatchReject = async () => {
    const ids = Array.from(selectedSuggestions);
    if (ids.length === 0) return;
    
    if (!confirm(`Reject ${ids.length} suggestion${ids.length > 1 ? 's' : ''}?`)) {
      return;
    }
    
    try {
      await api.batchRejectSuggestions(ids);
      alert(`✅ Rejected ${ids.length} suggestion${ids.length > 1 ? 's' : ''} successfully!`);
      setSelectedSuggestions(new Set());
      await loadData(); // Refresh data
    } catch (error) {
      alert(`❌ Failed to reject suggestions: ${error}`);
    }
  };

  const handleExport = () => {
    const selectedSuggs = suggestions.filter(s => 
      selectedSuggestions.size > 0 ? selectedSuggestions.has(s.id) : s.status === selectedStatus
    );
    
    const yaml = selectedSuggs.map(s => s.automation_yaml).join('\n\n# ---\n\n');
    const blob = new Blob([yaml], { type: 'text/yaml' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `ha-automations-${new Date().toISOString().split('T')[0]}.yaml`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
    
    alert(`✅ Exported ${selectedSuggs.length} automation${selectedSuggs.length > 1 ? 's' : ''} to YAML file!`);
  };

  // Apply all filters
  let filteredSuggestions = suggestions.filter(s => s.status === selectedStatus);
  
  // Search filter
  if (searchQuery) {
    const query = searchQuery.toLowerCase();
    filteredSuggestions = filteredSuggestions.filter(s =>
      s.title.toLowerCase().includes(query) ||
      s.description.toLowerCase().includes(query) ||
      s.automation_yaml.toLowerCase().includes(query)
    );
  }
  
  // Category filter
  if (categoryFilter) {
    filteredSuggestions = filteredSuggestions.filter(s => s.category === categoryFilter);
  }
  
  // Confidence filter
  if (minConfidenceFilter > 0) {
    filteredSuggestions = filteredSuggestions.filter(s => s.confidence >= minConfidenceFilter);
  }

  return (
    <>
      {/* Setup Wizard */}
      {showWizard && (
        <SetupWizard onComplete={handleWizardComplete} darkMode={darkMode} />
      )}

      <div className="space-y-6">
      {/* Hero Section */}
      <motion.div
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        className={`rounded-2xl shadow-xl p-8 ${
          darkMode
            ? 'bg-gradient-to-br from-blue-900 to-purple-900'
            : 'bg-gradient-to-br from-blue-500 to-purple-600'
        } text-white`}
      >
        <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
          <div>
            <h1 className="text-3xl md:text-4xl font-bold mb-2">
              🤖 AI Automation Suggestions
            </h1>
            <p className="text-blue-100 text-sm md:text-base">
              Intelligent automation recommendations powered by machine learning
            </p>
          </div>

          <motion.button
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.95 }}
            onClick={handleTriggerAnalysis}
            disabled={triggering || scheduleInfo?.is_running}
            className="px-6 py-3 bg-white text-blue-600 rounded-xl font-bold shadow-lg hover:shadow-xl transition-all disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {triggering || scheduleInfo?.is_running ? '⏳ Analyzing...' : '▶️ Run Analysis'}
          </motion.button>
        </div>

        {/* Schedule Info */}
        {scheduleInfo && (
          <div className="mt-6 grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className="bg-white/10 backdrop-blur rounded-lg p-3">
              <div className="text-xs text-blue-200">Next Run</div>
              <div className="text-sm font-bold mt-1">
                {scheduleInfo.next_run ? new Date(scheduleInfo.next_run).toLocaleString() : 'Not scheduled'}
              </div>
            </div>
            
            <div className="bg-white/10 backdrop-blur rounded-lg p-3">
              <div className="text-xs text-blue-200">Status</div>
              <div className="text-sm font-bold mt-1">
                {scheduleInfo.is_running ? '🔄 Running' : '✅ Ready'}
              </div>
            </div>

            {scheduleInfo.recent_jobs?.[0] && (
              <>
                <div className="bg-white/10 backdrop-blur rounded-lg p-3">
                  <div className="text-xs text-blue-200">Last Run</div>
                  <div className="text-sm font-bold mt-1">
                    {scheduleInfo.recent_jobs[0].suggestions_generated || 0} suggestions
                  </div>
                </div>
                
                <div className="bg-white/10 backdrop-blur rounded-lg p-3">
                  <div className="text-xs text-blue-200">Cost</div>
                  <div className="text-sm font-bold mt-1">
                    ${(scheduleInfo.recent_jobs[0].openai_cost_usd || 0).toFixed(4)}
                  </div>
                </div>
              </>
            )}
          </div>
        )}
      </motion.div>

      {/* Batch Actions Bar */}
      <AnimatePresence>
        <BatchActions
          selectedCount={selectedSuggestions.size}
          onApproveAll={handleBatchApprove}
          onRejectAll={handleBatchReject}
          onExport={handleExport}
          onClearSelection={() => setSelectedSuggestions(new Set())}
          darkMode={darkMode}
        />
      </AnimatePresence>

      {/* Search & Filters */}
      <SearchBar
        value={searchQuery}
        onChange={setSearchQuery}
        onCategoryFilter={setCategoryFilter}
        onConfidenceFilter={setMinConfidenceFilter}
        selectedCategory={categoryFilter}
        minConfidence={minConfidenceFilter}
        darkMode={darkMode}
      />

      {/* Status Tabs */}
      <div className="flex gap-2 overflow-x-auto pb-2">
        {(['pending', 'approved', 'deployed', 'rejected'] as const).map((status) => (
          <motion.button
            key={status}
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.95 }}
            onClick={() => setSelectedStatus(status)}
            className={`px-6 py-3 rounded-xl font-semibold transition-all whitespace-nowrap ${
              selectedStatus === status
                ? darkMode
                  ? 'bg-blue-600 text-white shadow-lg'
                  : 'bg-blue-500 text-white shadow-lg'
                : darkMode
                ? 'bg-gray-700 text-gray-300 hover:bg-gray-600'
                : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
            }`}
          >
            {status.charAt(0).toUpperCase() + status.slice(1)}
            <span className={`ml-2 px-2 py-0.5 rounded-full text-xs ${
              selectedStatus === status
                ? 'bg-white/20'
                : darkMode ? 'bg-gray-600' : 'bg-gray-200'
            }`}>
              {suggestions.filter(s => s.status === status).length}
            </span>
          </motion.button>
        ))}
      </div>

      {/* Error Banner */}
      {error && (
        <motion.div
          initial={{ opacity: 0, y: -10 }}
          animate={{ opacity: 1, y: 0 }}
          className="bg-red-100 dark:bg-red-900 border-2 border-red-400 dark:border-red-600 text-red-800 dark:text-red-200 px-6 py-4 rounded-xl"
        >
          <strong>⚠️ Error:</strong> {error}
        </motion.div>
      )}

      {/* Suggestions List */}
      <AnimatePresence mode="wait">
        {loading ? (
          <div className="grid gap-6">
            {[1, 2, 3].map((i) => (
              <div
                key={i}
                className={`h-64 rounded-2xl animate-pulse ${darkMode ? 'bg-gray-800' : 'bg-gray-200'}`}
              />
            ))}
          </div>
        ) : filteredSuggestions.length === 0 ? (
          <motion.div
            key="empty"
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            exit={{ opacity: 0, scale: 0.95 }}
            className={`text-center py-20 rounded-2xl ${darkMode ? 'bg-gray-800' : 'bg-white'} shadow-xl`}
          >
            <div className="text-8xl mb-6">🤖</div>
            <h3 className={`text-2xl font-bold mb-3 ${darkMode ? 'text-white' : 'text-gray-900'}`}>
              No {selectedStatus} suggestions
            </h3>
            <p className={`text-lg mb-8 ${darkMode ? 'text-gray-400' : 'text-gray-600'} max-w-md mx-auto`}>
              {selectedStatus === 'pending'
                ? 'Run an analysis to generate new automation suggestions based on your smart home usage patterns.'
                : `No ${selectedStatus} suggestions found.`}
            </p>
            {selectedStatus === 'pending' && (
              <motion.button
                whileHover={{ scale: 1.05 }}
                whileTap={{ scale: 0.95 }}
                onClick={handleTriggerAnalysis}
                disabled={triggering}
                className="px-8 py-4 bg-gradient-to-r from-blue-500 to-purple-600 hover:from-blue-600 hover:to-purple-700 text-white text-lg font-bold rounded-xl shadow-2xl transition-all disabled:opacity-50"
              >
                {triggering ? '⏳ Running...' : '🚀 Generate Suggestions Now'}
              </motion.button>
            )}
          </motion.div>
        ) : (
          <motion.div
            key="list"
            className="grid gap-6"
          >
            {filteredSuggestions.map((suggestion, index) => (
              <motion.div
                key={suggestion.id}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: index * 0.1 }}
              >
                {/* Selection Checkbox for Batch Operations */}
                {suggestion.status === 'pending' && (
                  <div className="flex items-start gap-3">
                    <input
                      type="checkbox"
                      checked={selectedSuggestions.has(suggestion.id)}
                      onChange={() => toggleSelection(suggestion.id)}
                      className="mt-6 w-5 h-5 rounded border-gray-300 text-blue-600 focus:ring-blue-500 cursor-pointer"
                    />
                    <div className="flex-1">
                      <SuggestionCard
                        suggestion={suggestion}
                        onApprove={handleApprove}
                        onReject={handleReject}
                        onEdit={handleEdit}
                        onDeploy={handleDeploy}
                        darkMode={darkMode}
                      />
                    </div>
                  </div>
                )}
                {suggestion.status !== 'pending' && (
                  <SuggestionCard
                    suggestion={suggestion}
                    onApprove={handleApprove}
                    onReject={handleReject}
                    onEdit={handleEdit}
                    onDeploy={handleDeploy}
                    darkMode={darkMode}
                  />
                )}
              </motion.div>
            ))}
          </motion.div>
        )}
      </AnimatePresence>

      {/* Info Footer */}
      <div className={`rounded-xl p-6 ${darkMode ? 'bg-blue-900/30' : 'bg-blue-50'} border-2 ${darkMode ? 'border-blue-700' : 'border-blue-200'}`}>
        <div className={`text-sm ${darkMode ? 'text-blue-200' : 'text-blue-900'}`}>
          <strong>💡 How it works:</strong> The AI analyzes 30 days of your Home Assistant usage patterns 
          and generates automation suggestions. Each suggestion includes confidence scores and fully-tested YAML code.
          <br /><br />
          <strong>🔒 Privacy:</strong> Only device IDs are analyzed (e.g., "light.bedroom"). No personal data leaves your network.
          <br />
          <strong>💰 Cost:</strong> ~$0.0025 per analysis run (~$0.075/month for daily automation)
        </div>
      </div>

      {/* Floating Action Buttons */}
      <div className="fixed bottom-8 right-8 flex flex-col gap-3">
        {/* Export All Button */}
        <motion.button
          whileHover={{ scale: 1.1 }}
          whileTap={{ scale: 0.9 }}
          onClick={handleExport}
          className={`p-4 rounded-full shadow-2xl ${
            darkMode
              ? 'bg-blue-600 hover:bg-blue-500'
              : 'bg-blue-500 hover:bg-blue-600'
          } text-white`}
          title="Export all suggestions to YAML"
        >
          <span className="text-2xl">💾</span>
        </motion.button>

        {/* Back to Top */}
        <motion.button
          whileHover={{ scale: 1.1 }}
          whileTap={{ scale: 0.9 }}
          onClick={() => window.scrollTo({ top: 0, behavior: 'smooth' })}
          className={`p-4 rounded-full shadow-2xl ${
            darkMode
              ? 'bg-gray-700 hover:bg-gray-600'
              : 'bg-gray-200 hover:bg-gray-300'
          }`}
          title="Back to top"
        >
          <span className="text-2xl">⬆️</span>
        </motion.button>

        {/* Help/Reset Wizard */}
        <motion.button
          whileHover={{ scale: 1.1 }}
          whileTap={{ scale: 0.9 }}
          onClick={() => setShowWizard(true)}
          className={`p-4 rounded-full shadow-2xl ${
            darkMode
              ? 'bg-purple-600 hover:bg-purple-500'
              : 'bg-purple-500 hover:bg-purple-600'
          } text-white`}
          title="Show setup wizard"
        >
          <span className="text-2xl">❓</span>
        </motion.button>
      </div>
    </div>
    </>
  );
};


/**
 * Main Dashboard - Suggestion Feed
 * Beautiful card-based interface for viewing and managing AI suggestions
 */

import React, { useEffect, useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import toast from 'react-hot-toast';
import { useAppStore } from '../store';
import { useSelection } from '../context/SelectionContext';
import { useKeyboardShortcuts } from '../hooks/useKeyboardShortcuts';
import { SuggestionCard } from '../components/SuggestionCard';
import { SetupWizard } from '../components/SetupWizard';
import { BatchActions } from '../components/BatchActions';
import { SearchBar } from '../components/SearchBar';
import { AnalysisStatusButton } from '../components/AnalysisStatusButton';
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
  const [searchQuery, setSearchQuery] = useState('');
  const [categoryFilter, setCategoryFilter] = useState<string | null>(null);
  const [selectedConfidenceLevels, setSelectedConfidenceLevels] = useState<string[]>([]);
  
  // Selection Context
  const {
    selectedCount,
    selectItem,
    deselectItem,
    clearSelection,
    isSelected,
    getSelectedIds,
  } = useSelection();

  const loadData = async () => {
    try {
      setLoading(true);
      setError(null);

      const [suggestionsRes, scheduleRes] = await Promise.all([
        api.getSuggestions(selectedStatus),
        api.getScheduleInfo()
      ]);

      setSuggestions(suggestionsRes.data.suggestions || []);
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
      // Toast notification is handled by AnalysisStatusButton
      setTimeout(loadData, 2000);
    } catch (err) {
      // Error toast is handled by AnalysisStatusButton
      throw err; // Re-throw so AnalysisStatusButton can handle the error
    } finally {
      setTriggering(false);
    }
  };

  const handleApprove = async (id: number) => {
    try {
      await api.approveSuggestion(id);
      toast.success('✅ Suggestion approved successfully!');
      await loadData(); // Refresh data
    } catch (error) {
      const message = error instanceof Error ? error.message : 'Unknown error';
      toast.error(`❌ Failed to approve suggestion: ${message}`);
    }
  };

  const handleReject = async (id: number) => {
    const reason = prompt('Why are you rejecting this suggestion? (optional)');
    try {
      await api.rejectSuggestion(id, reason || undefined);
      toast.success('✅ Suggestion rejected successfully!');
      await loadData(); // Refresh data
    } catch (error) {
      const message = error instanceof Error ? error.message : 'Unknown error';
      toast.error(`❌ Failed to reject suggestion: ${message}`);
    }
  };

  const handleEdit = async (id: number) => {
    const suggestion = suggestions.find(s => s.id === id);
    if (!suggestion) return;
    
    const newYaml = prompt('Edit YAML automation code:', suggestion.automation_yaml);
    if (newYaml && newYaml !== suggestion.automation_yaml) {
      try {
        await api.updateSuggestion(id, { automation_yaml: newYaml });
        toast.success('✅ Suggestion updated successfully!');
        await loadData(); // Refresh data
      } catch (error) {
        const message = error instanceof Error ? error.message : 'Unknown error';
        toast.error(`❌ Failed to update suggestion: ${message}`);
      }
    }
  };

  const handleDeploy = async (id: number) => {
    if (!confirm('Deploy this automation to Home Assistant?')) {
      return;
    }
    
    try {
      const result = await api.deploySuggestion(id);
      toast.success(`✅ ${result.message}\n\nAutomation ID: ${result.data?.automation_id}`, {
        duration: 6000,
      });
      await loadData(); // Refresh data
    } catch (error) {
      const message = error instanceof Error ? error.message : 'Unknown error';
      toast.error(`❌ Failed to deploy automation: ${message}`);
    }
  };

  const handleWizardComplete = () => {
    localStorage.setItem('setup_complete', 'true');
    setShowWizard(false);
  };


  const handleBatchApprove = async (ids?: number[]) => {
    const targetIds = ids || getSelectedIds();
    if (targetIds.length === 0) return;
    
    try {
      await api.batchApproveSuggestions(targetIds);
      toast.success(`✅ Approved ${targetIds.length} suggestion${targetIds.length > 1 ? 's' : ''} successfully!`);
      clearSelection();
      await loadData(); // Refresh data
    } catch (error) {
      const message = error instanceof Error ? error.message : 'Unknown error';
      toast.error(`❌ Failed to approve suggestions: ${message}`);
      throw error; // Re-throw for modal error handling
    }
  };

  const handleBatchReject = async (ids?: number[]) => {
    const targetIds = ids || getSelectedIds();
    if (targetIds.length === 0) return;
    
    try {
      await api.batchRejectSuggestions(targetIds);
      toast.success(`✅ Rejected ${targetIds.length} suggestion${targetIds.length > 1 ? 's' : ''} successfully!`);
      clearSelection();
      await loadData(); // Refresh data
    } catch (error) {
      const message = error instanceof Error ? error.message : 'Unknown error';
      toast.error(`❌ Failed to reject suggestions: ${message}`);
      throw error; // Re-throw for modal error handling
    }
  };

  const handleExport = () => {
    const selectedSuggs = suggestions.filter(s => 
      selectedCount > 0 ? isSelected(s.id) : s.status === selectedStatus
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
    
    toast.success(`✅ Exported ${selectedSuggs.length} automation${selectedSuggs.length > 1 ? 's' : ''} to YAML file!`);
  };

  // Keyboard Shortcuts (moved after function definitions)
  const keyboardShortcuts = useKeyboardShortcuts({
    availableIds: suggestions.filter(s => s.status === 'pending').map(s => s.id),
    onBatchApprove: handleBatchApprove,
    onBatchReject: handleBatchReject,
    onSelectAll: () => {
      const pendingIds = suggestions.filter(s => s.status === 'pending').map(s => s.id);
      if (pendingIds.length > 0) {
        // Select all pending suggestions
        pendingIds.forEach(id => selectItem(id));
      }
    },
  });

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
  
  // Confidence level filter
  if (selectedConfidenceLevels.length > 0) {
    filteredSuggestions = filteredSuggestions.filter(s => {
      const confidenceLevel = s.confidence >= 90 ? 'high' : s.confidence >= 70 ? 'medium' : 'low';
      return selectedConfidenceLevels.includes(confidenceLevel);
    });
  }

  // Calculate suggestion counts for filter pills
  const getSuggestionCounts = () => {
    const baseSuggestions = suggestions.filter(s => s.status === selectedStatus);
    
    return {
      categories: {
        energy: baseSuggestions.filter(s => s.category === 'energy').length,
        comfort: baseSuggestions.filter(s => s.category === 'comfort').length,
        security: baseSuggestions.filter(s => s.category === 'security').length,
        convenience: baseSuggestions.filter(s => s.category === 'convenience').length,
      },
      confidence: {
        high: baseSuggestions.filter(s => s.confidence >= 90).length,
        medium: baseSuggestions.filter(s => s.confidence >= 70 && s.confidence < 90).length,
        low: baseSuggestions.filter(s => s.confidence < 70).length,
      }
    };
  };

  return (
    <>
      {/* Setup Wizard */}
      {showWizard && (
        <SetupWizard onComplete={handleWizardComplete} darkMode={darkMode} />
      )}

      <div className="space-y-4">
      {/* Compact Header */}
      <div className={`border-b ${darkMode ? 'border-gray-700' : 'border-gray-200'} pb-3`}>
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-4">
            <h1 className={`text-lg font-semibold ${darkMode ? 'text-white' : 'text-gray-900'}`}>
              AI Automation Suggestions
            </h1>
            <span className={`text-sm ${darkMode ? 'text-gray-400' : 'text-gray-500'}`}>
              {suggestions.length} suggestions
            </span>
          </div>
          
          <div className="flex items-center gap-3">
            <div className="flex items-center gap-2 text-sm">
              <div className={`w-2 h-2 ${scheduleInfo?.is_running ? 'bg-yellow-500' : 'bg-green-500'}`} />
              <span className={darkMode ? 'text-gray-300' : 'text-gray-600'}>
                {scheduleInfo?.is_running ? 'Running' : 'Ready'}
              </span>
            </div>
            
            <AnalysisStatusButton
              status={
                scheduleInfo?.is_running ? 'running' :
                triggering ? 'running' :
                'ready'
              }
              progress={scheduleInfo?.is_running ? 50 : 0}
              estimatedTime={scheduleInfo?.is_running ? 120 : undefined}
              onRunAnalysis={handleTriggerAnalysis}
              darkMode={darkMode}
              disabled={triggering || scheduleInfo?.is_running}
            />
          </div>
        </div>
      </div>

      {/* Enhanced Batch Actions Bar */}
      <AnimatePresence>
        <BatchActions
          selectedCount={selectedCount}
          onApproveAll={() => handleBatchApprove()}
          onRejectAll={() => handleBatchReject()}
          onExport={handleExport}
          onClearSelection={clearSelection}
          darkMode={darkMode}
          keyboardShortcuts={keyboardShortcuts.shortcuts}
        />
      </AnimatePresence>

      {/* Enhanced Search & Filters */}
      <SearchBar
        value={searchQuery}
        onChange={setSearchQuery}
        onCategoryFilter={setCategoryFilter}
        onConfidenceFilter={setSelectedConfidenceLevels}
        selectedCategory={categoryFilter}
        selectedConfidenceLevels={selectedConfidenceLevels}
        darkMode={darkMode}
        suggestionCounts={getSuggestionCounts()}
      />

      {/* Status Tabs */}
      <div className="flex gap-1 overflow-x-auto pb-1">
        {(['pending', 'approved', 'deployed', 'rejected'] as const).map((status) => (
          <button
            key={status}
            onClick={() => setSelectedStatus(status)}
            className={`px-3 py-1 text-sm font-medium transition-colors whitespace-nowrap ${
              selectedStatus === status
                ? darkMode
                  ? 'bg-blue-600 text-white'
                  : 'bg-blue-500 text-white'
                : darkMode
                ? 'bg-gray-700 text-gray-300 hover:bg-gray-600'
                : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
            }`}
          >
            {status.charAt(0).toUpperCase() + status.slice(1)}
            <span className={`ml-1 px-1 text-xs ${
              selectedStatus === status
                ? 'bg-white/20'
                : darkMode ? 'bg-gray-600' : 'bg-gray-200'
            }`}>
              {suggestions.filter(s => s.status === status).length}
            </span>
          </button>
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
                {/* Enhanced Selection for Batch Operations */}
                {suggestion.status === 'pending' && (
                  <div className="flex items-start gap-3">
                    <input
                      type="checkbox"
                      checked={isSelected(suggestion.id)}
                      onChange={(e) => {
                        if (e.target.checked) {
                          selectItem(suggestion.id);
                        } else {
                          deselectItem(suggestion.id);
                        }
                      }}
                      className="mt-6 w-5 h-5 rounded border-gray-300 text-blue-600 focus:ring-blue-500 cursor-pointer"
                      aria-label={`Select suggestion: ${suggestion.title}`}
                    />
                    <div className="flex-1">
                      <SuggestionCard
                        suggestion={suggestion}
                        onApprove={handleApprove}
                        onReject={handleReject}
                        onEdit={handleEdit}
                        onDeploy={handleDeploy}
                        darkMode={darkMode}
                        isSelected={isSelected(suggestion.id)}
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
                    isSelected={false}
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


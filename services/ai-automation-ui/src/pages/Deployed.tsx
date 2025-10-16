/**
 * Deployed Automations Page
 * Manage deployed automations from Home Assistant
 */

import React, { useEffect, useState } from 'react';
import { motion } from 'framer-motion';
import { useAppStore } from '../store';
import api from '../services/api';

interface Automation {
  entity_id: string;
  state: string;
  attributes: {
    friendly_name?: string;
    last_triggered?: string;
    mode?: string;
  };
}

export const Deployed: React.FC = () => {
  const { darkMode } = useAppStore();
  const [automations, setAutomations] = useState<Automation[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadAutomations();
  }, []);

  const loadAutomations = async () => {
    try {
      setLoading(true);
      const result = await api.listDeployedAutomations();
      setAutomations(result.data || []);
    } catch (error) {
      console.error('Failed to load automations:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleToggle = async (automationId: string, currentState: string) => {
    try {
      if (currentState === 'on') {
        await api.disableAutomation(automationId);
        alert(`✅ Disabled ${automationId}`);
      } else {
        await api.enableAutomation(automationId);
        alert(`✅ Enabled ${automationId}`);
      }
      await loadAutomations(); // Refresh
    } catch (error) {
      alert(`❌ Failed to toggle automation: ${error}`);
    }
  };

  const handleTrigger = async (automationId: string) => {
    try {
      await api.triggerAutomation(automationId);
      alert(`✅ Triggered ${automationId}`);
    } catch (error) {
      alert(`❌ Failed to trigger automation: ${error}`);
    }
  };

  return (
    <div className="space-y-6">
      <motion.div
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
      >
        <h1 className={`text-3xl font-bold mb-2 ${darkMode ? 'text-white' : 'text-gray-900'}`}>
          🚀 Deployed Automations
        </h1>
        <p className={darkMode ? 'text-gray-400' : 'text-gray-600'}>
          Manage automations deployed to Home Assistant
        </p>
      </motion.div>

      {/* Automations List */}
      {loading ? (
        <div className={`text-center py-12 ${darkMode ? 'text-gray-400' : 'text-gray-600'}`}>
          Loading deployed automations...
        </div>
      ) : automations.length === 0 ? (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className={`rounded-2xl shadow-xl p-8 text-center ${
            darkMode ? 'bg-gray-800' : 'bg-white'
          }`}
        >
          <div className="text-6xl mb-4">🚀</div>
          <h2 className={`text-2xl font-bold mb-4 ${darkMode ? 'text-white' : 'text-gray-900'}`}>
            No Deployed Automations Yet
          </h2>
          <p className={`text-lg mb-6 ${darkMode ? 'text-gray-400' : 'text-gray-600'}`}>
            Approve suggestions and deploy them to see them here!
          </p>
        </motion.div>
      ) : (
        <div className="space-y-4">
          {automations.map((automation, index) => (
            <motion.div
              key={automation.entity_id}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: index * 0.05 }}
              className={`rounded-xl shadow-lg p-6 ${
                darkMode ? 'bg-gray-800' : 'bg-white'
              }`}
            >
              <div className="flex items-center justify-between">
                <div className="flex-1">
                  <h3 className={`text-lg font-bold mb-1 ${darkMode ? 'text-white' : 'text-gray-900'}`}>
                    {automation.attributes.friendly_name || automation.entity_id}
                  </h3>
                  <p className={`text-sm ${darkMode ? 'text-gray-400' : 'text-gray-600'}`}>
                    {automation.entity_id}
                  </p>
                  {automation.attributes.last_triggered && (
                    <p className={`text-xs mt-2 ${darkMode ? 'text-gray-500' : 'text-gray-500'}`}>
                      Last triggered: {new Date(automation.attributes.last_triggered).toLocaleString()}
                    </p>
                  )}
                </div>
                
                <div className="flex gap-3 items-center">
                  {/* Status Badge */}
                  <div className={`px-3 py-1 rounded-full text-sm font-medium ${
                    automation.state === 'on'
                      ? 'bg-green-100 dark:bg-green-900 text-green-800 dark:text-green-200'
                      : 'bg-gray-100 dark:bg-gray-700 text-gray-800 dark:text-gray-200'
                  }`}>
                    {automation.state === 'on' ? '✅ Enabled' : '⏸️ Disabled'}
                  </div>
                  
                  {/* Toggle Button */}
                  <motion.button
                    whileHover={{ scale: 1.05 }}
                    whileTap={{ scale: 0.95 }}
                    onClick={() => handleToggle(automation.entity_id, automation.state)}
                    className={`px-4 py-2 rounded-lg font-medium ${
                      automation.state === 'on'
                        ? darkMode
                          ? 'bg-gray-700 hover:bg-gray-600 text-white'
                          : 'bg-gray-200 hover:bg-gray-300 text-gray-900'
                        : 'bg-green-500 hover:bg-green-600 text-white'
                    }`}
                  >
                    {automation.state === 'on' ? 'Disable' : 'Enable'}
                  </motion.button>
                  
                  {/* Trigger Button */}
                  <motion.button
                    whileHover={{ scale: 1.05 }}
                    whileTap={{ scale: 0.95 }}
                    onClick={() => handleTrigger(automation.entity_id)}
                    className={`px-4 py-2 rounded-lg font-medium ${
                      darkMode
                        ? 'bg-blue-600 hover:bg-blue-500 text-white'
                        : 'bg-blue-500 hover:bg-blue-600 text-white'
                    }`}
                  >
                    ▶️ Trigger
                  </motion.button>
                </div>
              </div>
            </motion.div>
          ))}
        </div>
      )}

      {/* Refresh Button */}
      <motion.button
        whileHover={{ scale: 1.02 }}
        whileTap={{ scale: 0.98 }}
        onClick={loadAutomations}
        className={`w-full px-6 py-3 rounded-xl font-semibold shadow-lg transition-all ${
          darkMode
            ? 'bg-gray-700 hover:bg-gray-600 text-white'
            : 'bg-gray-200 hover:bg-gray-300 text-gray-900'
        }`}
      >
        🔄 Refresh List
      </motion.button>
    </div>
  );
};

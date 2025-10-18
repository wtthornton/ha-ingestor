/**
 * Pattern Explorer Page
 * Visualize detected usage patterns
 */

import React, { useEffect, useState } from 'react';
import { motion } from 'framer-motion';
import { useAppStore } from '../store';
import api from '../services/api';
import type { Pattern } from '../types';
import { PatternTypeChart, ConfidenceDistributionChart, TopDevicesChart } from '../components/PatternChart';

export const Patterns: React.FC = () => {
  const { darkMode } = useAppStore();
  const [patterns, setPatterns] = useState<Pattern[]>([]);
  const [stats, setStats] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [deviceNames, setDeviceNames] = useState<Record<string, string>>({});

  useEffect(() => {
    const loadPatterns = async () => {
      try {
      const [patternsRes, statsRes] = await Promise.all([
        api.getPatterns(undefined, 0.7),
        api.getPatternStats()
      ]);
      const patternsData = patternsRes.data.patterns || [];
      setPatterns(patternsData);
      setStats(statsRes.data || statsRes);

      // Load device names for the patterns
      if (patternsData.length > 0) {
        const uniqueDeviceIds = [...new Set(patternsData.map(p => p.device_id))];
        const names = await api.getDeviceNames(uniqueDeviceIds);
        setDeviceNames(names);
      }
      } catch (err) {
        console.error('Failed to load patterns:', err);
      } finally {
        setLoading(false);
      }
    };

    loadPatterns();
  }, []);

  const getPatternIcon = (type: string) => {
    const icons = {
      time_of_day: '⏰',
      co_occurrence: '🔗',
      anomaly: '⚠️',
    };
    return icons[type as keyof typeof icons] || '📊';
  };

  const getFallbackName = (deviceId: string) => {
    if (deviceId.includes('+')) {
      const parts = deviceId.split('+');
      if (parts.length === 2) {
        return `Co-occurrence (${parts[0].substring(0, 8)}... + ${parts[1].substring(0, 8)}...)`;
      }
    }
    
    // Try to create a more descriptive name based on the device ID pattern
    if (deviceId.length === 32) {
      // Looks like a hash - create a more friendly name
      return `Device ${deviceId.substring(0, 8)}...`;
    }
    
    return deviceId.length > 20 ? `${deviceId.substring(0, 20)}...` : deviceId;
  };

  return (
    <div className="space-y-6">
      <motion.div
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
      >
        <h1 className={`text-3xl font-bold mb-2 ${darkMode ? 'text-white' : 'text-gray-900'}`}>
          📊 Detected Patterns
        </h1>
        <p className={darkMode ? 'text-gray-400' : 'text-gray-600'}>
          Usage patterns detected by machine learning analysis
        </p>
      </motion.div>

      {/* Stats Cards */}
      {stats && (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className={`p-6 rounded-xl ${darkMode ? 'bg-gray-800' : 'bg-white'} shadow-lg`}
          >
            <div className="text-3xl font-bold bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent">
              {stats.total_patterns || 0}
            </div>
            <div className={`text-sm mt-1 ${darkMode ? 'text-gray-400' : 'text-gray-600'}`}>
              Total Patterns
            </div>
          </motion.div>

          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.1 }}
            className={`p-6 rounded-xl ${darkMode ? 'bg-gray-800' : 'bg-white'} shadow-lg`}
          >
            <div className="text-3xl font-bold bg-gradient-to-r from-green-600 to-blue-600 bg-clip-text text-transparent">
              {stats.unique_devices || 0}
            </div>
            <div className={`text-sm mt-1 ${darkMode ? 'text-gray-400' : 'text-gray-600'}`}>
              Devices
            </div>
          </motion.div>

          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.2 }}
            className={`p-6 rounded-xl ${darkMode ? 'bg-gray-800' : 'bg-white'} shadow-lg`}
          >
            <div className="text-3xl font-bold bg-gradient-to-r from-yellow-600 to-red-600 bg-clip-text text-transparent">
              {Math.round((stats.avg_confidence || 0) * 100)}%
            </div>
            <div className={`text-sm mt-1 ${darkMode ? 'text-gray-400' : 'text-gray-600'}`}>
              Avg Confidence
            </div>
          </motion.div>

          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.3 }}
            className={`p-6 rounded-xl ${darkMode ? 'bg-gray-800' : 'bg-white'} shadow-lg`}
          >
            <div className="text-3xl font-bold bg-gradient-to-r from-purple-600 to-pink-600 bg-clip-text text-transparent">
              {Object.keys(stats.by_type || {}).length}
            </div>
            <div className={`text-sm mt-1 ${darkMode ? 'text-gray-400' : 'text-gray-600'}`}>
              Pattern Types
            </div>
          </motion.div>
        </div>
      )}

      {/* Charts */}
      {!loading && patterns.length > 0 && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <div className={`p-6 rounded-xl ${darkMode ? 'bg-gray-800' : 'bg-white'} shadow-lg`}>
            <PatternTypeChart patterns={patterns} darkMode={darkMode} />
          </div>
          <div className={`p-6 rounded-xl ${darkMode ? 'bg-gray-800' : 'bg-white'} shadow-lg`}>
            <ConfidenceDistributionChart patterns={patterns} darkMode={darkMode} />
          </div>
          <div className={`p-6 rounded-xl ${darkMode ? 'bg-gray-800' : 'bg-white'} shadow-lg lg:col-span-2`}>
            <TopDevicesChart patterns={patterns} darkMode={darkMode} />
          </div>
        </div>
      )}

      {/* Pattern List */}
      <div className="grid gap-4">
        {loading ? (
          <div className={`text-center py-12 ${darkMode ? 'text-gray-400' : 'text-gray-600'}`}>
            Loading patterns...
          </div>
        ) : patterns.length === 0 ? (
          <div className={`text-center py-12 rounded-xl ${darkMode ? 'bg-gray-800' : 'bg-white'} shadow`}>
            <div className="text-6xl mb-4">📊</div>
            <div className={`text-xl font-bold ${darkMode ? 'text-white' : 'text-gray-900'}`}>
              No patterns detected yet
            </div>
            <p className={`mt-2 ${darkMode ? 'text-gray-400' : 'text-gray-600'}`}>
              Run an analysis to detect patterns in your smart home usage
            </p>
          </div>
        ) : (
          patterns.slice(0, 20).map((pattern, idx) => (
            <motion.div
              key={pattern.id}
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: idx * 0.05 }}
              className={`p-4 rounded-xl ${darkMode ? 'bg-gray-800' : 'bg-white'} shadow hover:shadow-lg transition-shadow`}
            >
              <div className="flex items-start justify-between">
                <div className="flex items-start gap-3">
                  <div className="text-3xl">{getPatternIcon(pattern.pattern_type)}</div>
                  <div>
                    <div className={`font-semibold ${darkMode ? 'text-white' : 'text-gray-900'}`}>
                      {deviceNames[pattern.device_id] || getFallbackName(pattern.device_id)}
                    </div>
                    <div className={`text-sm ${darkMode ? 'text-gray-400' : 'text-gray-600'}`}>
                      {pattern.pattern_type.replace('_', ' ')} • {pattern.occurrences} occurrences
                    </div>
                    {deviceNames[pattern.device_id] && (
                      <div className={`text-xs ${darkMode ? 'text-gray-500' : 'text-gray-500'}`}>
                        ID: {pattern.device_id}
                      </div>
                    )}
                  </div>
                </div>

                <div className="text-right">
                  <div className={`text-lg font-bold ${darkMode ? 'text-white' : 'text-gray-900'}`}>
                    {Math.round(pattern.confidence * 100)}%
                  </div>
                  <div className="text-xs text-gray-500">confidence</div>
                </div>
              </div>
            </motion.div>
          ))
        )}
      </div>
    </div>
  );
};


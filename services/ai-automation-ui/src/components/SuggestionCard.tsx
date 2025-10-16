/**
 * Beautiful Suggestion Card Component
 * Displays AI-generated automation suggestions with swipe-to-approve
 */

import React, { useState } from 'react';
import { motion } from 'framer-motion';
import type { Suggestion } from '../types';
import { ConfidenceMeter } from './ConfidenceMeter';

interface SuggestionCardProps {
  suggestion: Suggestion;
  onApprove?: (id: number) => void;
  onReject?: (id: number) => void;
  onEdit?: (id: number) => void;
  onDeploy?: (id: number) => void;
  darkMode?: boolean;
}

export const SuggestionCard: React.FC<SuggestionCardProps> = ({
  suggestion,
  onApprove,
  onReject,
  onEdit,
  onDeploy,
  darkMode = false
}) => {
  const [showYaml, setShowYaml] = useState(false);

  const getCategoryColor = () => {
    const colors = {
      energy: 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200 border-green-300 dark:border-green-700',
      comfort: 'bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200 border-blue-300 dark:border-blue-700',
      security: 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200 border-red-300 dark:border-red-700',
      convenience: 'bg-purple-100 text-purple-800 dark:bg-purple-900 dark:text-purple-200 border-purple-300 dark:border-purple-700',
    };
    return colors[suggestion.category || 'convenience'];
  };

  const getCategoryIcon = () => {
    const icons = {
      energy: '🌱',
      comfort: '💙',
      security: '🔐',
      convenience: '✨',
    };
    return icons[suggestion.category || 'convenience'];
  };

  const getPriorityColor = () => {
    const colors = {
      high: 'text-red-600 dark:text-red-400',
      medium: 'text-yellow-600 dark:text-yellow-400',
      low: 'text-green-600 dark:text-green-400',
    };
    return colors[suggestion.priority || 'medium'];
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, scale: 0.95 }}
      className={`rounded-2xl shadow-lg border overflow-hidden ${
        darkMode
          ? 'bg-gray-800 border-gray-700'
          : 'bg-white border-gray-200'
      }`}
    >
      {/* Header with Category Badge */}
      <div className={`p-6 ${darkMode ? 'bg-gray-750' : 'bg-gradient-to-r from-blue-50 to-purple-50'}`}>
        <div className="flex justify-between items-start mb-3">
          <div className="flex-1">
            <h3 className={`text-xl font-bold mb-2 ${darkMode ? 'text-white' : 'text-gray-900'}`}>
              {suggestion.title}
            </h3>
            <p className={`text-sm ${darkMode ? 'text-gray-300' : 'text-gray-700'}`}>
              {suggestion.description}
            </p>
          </div>
          
          <div className="ml-4 flex flex-col gap-2 items-end">
            {suggestion.category && (
              <span className={`px-3 py-1 rounded-full text-xs font-semibold border ${getCategoryColor()}`}>
                {getCategoryIcon()} {suggestion.category}
              </span>
            )}
            {suggestion.priority && (
              <span className={`text-xs font-bold uppercase ${getPriorityColor()}`}>
                {suggestion.priority}
              </span>
            )}
          </div>
        </div>

        {/* Confidence Meter */}
        <ConfidenceMeter confidence={suggestion.confidence} darkMode={darkMode} />
      </div>

      {/* Body */}
      <div className="p-6 space-y-4">
        {/* YAML Preview */}
        <div>
          <button
            onClick={() => setShowYaml(!showYaml)}
            className={`w-full text-left px-4 py-3 rounded-lg font-medium transition-all ${
              darkMode
                ? 'bg-gray-700 hover:bg-gray-600 text-white'
                : 'bg-gray-100 hover:bg-gray-200 text-gray-900'
            }`}
          >
            <span className="flex items-center justify-between">
              <span>
                {showYaml ? '▼' : '▶'} Home Assistant Automation
              </span>
              <span className="text-xs opacity-70">
                {showYaml ? 'Hide' : 'Show'} YAML
              </span>
            </span>
          </button>

          {showYaml && (
            <motion.div
              initial={{ height: 0, opacity: 0 }}
              animate={{ height: 'auto', opacity: 1 }}
              exit={{ height: 0, opacity: 0 }}
              transition={{ duration: 0.2 }}
            >
              <pre className={`mt-2 p-4 rounded-lg text-xs overflow-x-auto font-mono ${
                darkMode ? 'bg-gray-900 text-green-400' : 'bg-gray-50 text-gray-800'
              } border ${darkMode ? 'border-gray-700' : 'border-gray-200'}`}>
                {suggestion.automation_yaml}
              </pre>
            </motion.div>
          )}
        </div>

        {/* Action Buttons (Only for pending suggestions) */}
        {suggestion.status === 'pending' && onApprove && onReject && (
          <div className="flex gap-3">
            <motion.button
              whileHover={{ scale: 1.02 }}
              whileTap={{ scale: 0.98 }}
              onClick={() => onApprove(suggestion.id)}
              className="flex-1 px-6 py-3 bg-gradient-to-r from-green-500 to-green-600 hover:from-green-600 hover:to-green-700 text-white rounded-xl font-semibold shadow-lg transition-all"
            >
              ✅ Approve
            </motion.button>

            {onEdit && (
              <motion.button
                whileHover={{ scale: 1.02 }}
                whileTap={{ scale: 0.98 }}
                onClick={() => onEdit(suggestion.id)}
                className={`px-6 py-3 rounded-xl font-semibold shadow-lg transition-all ${
                  darkMode
                    ? 'bg-gray-700 hover:bg-gray-600 text-white'
                    : 'bg-gray-200 hover:bg-gray-300 text-gray-900'
                }`}
              >
                ✏️ Edit
              </motion.button>
            )}

            <motion.button
              whileHover={{ scale: 1.02 }}
              whileTap={{ scale: 0.98 }}
              onClick={() => onReject(suggestion.id)}
              className="flex-1 px-6 py-3 bg-gradient-to-r from-red-500 to-red-600 hover:from-red-600 hover:to-red-700 text-white rounded-xl font-semibold shadow-lg transition-all"
            >
              ❌ Reject
            </motion.button>
          </div>
        )}

        {/* Deploy Button for approved suggestions */}
        {suggestion.status === 'approved' && onDeploy && (
          <motion.button
            whileHover={{ scale: 1.02 }}
            whileTap={{ scale: 0.98 }}
            onClick={() => onDeploy(suggestion.id)}
            className="w-full px-6 py-4 bg-gradient-to-r from-blue-500 to-purple-600 hover:from-blue-600 hover:to-purple-700 text-white rounded-xl font-bold shadow-2xl transition-all text-lg"
          >
            🚀 Deploy to Home Assistant
          </motion.button>
        )}

        {/* Status Badge for deployed/rejected */}
        {(suggestion.status === 'deployed' || suggestion.status === 'rejected') && (
          <div className={`text-center py-3 rounded-lg font-semibold ${
            suggestion.status === 'deployed' ? 'bg-blue-100 dark:bg-blue-900 text-blue-800 dark:text-blue-200' :
            'bg-gray-100 dark:bg-gray-700 text-gray-800 dark:text-gray-200'
          }`}>
            {suggestion.status === 'deployed' && '🚀 Deployed to Home Assistant'}
            {suggestion.status === 'rejected' && '❌ Rejected'}
          </div>
        )}

        {/* Metadata Footer */}
        <div className={`text-xs ${darkMode ? 'text-gray-400' : 'text-gray-500'} pt-3 border-t ${darkMode ? 'border-gray-700' : 'border-gray-200'}`}>
          <div className="flex justify-between">
            <span>Created: {new Date(suggestion.created_at).toLocaleString()}</span>
            <span>ID: #{suggestion.id}</span>
          </div>
        </div>
      </div>
    </motion.div>
  );
};


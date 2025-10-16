/**
 * Batch Actions Component
 * Select multiple suggestions and perform bulk operations
 */

import React from 'react';
import { motion } from 'framer-motion';

interface BatchActionsProps {
  selectedCount: number;
  onApproveAll: () => void;
  onRejectAll: () => void;
  onExport: () => void;
  onClearSelection: () => void;
  darkMode?: boolean;
}

export const BatchActions: React.FC<BatchActionsProps> = ({
  selectedCount,
  onApproveAll,
  onRejectAll,
  onExport,
  onClearSelection,
  darkMode = false
}) => {
  if (selectedCount === 0) return null;

  return (
    <motion.div
      initial={{ opacity: 0, y: -10 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -10 }}
      className={`sticky top-20 z-40 p-4 rounded-xl shadow-2xl border-2 ${
        darkMode
          ? 'bg-gray-800 border-blue-500'
          : 'bg-white border-blue-400'
      }`}
    >
      <div className="flex flex-col md:flex-row items-center justify-between gap-4">
        <div className={`font-semibold ${darkMode ? 'text-white' : 'text-gray-900'}`}>
          {selectedCount} suggestion{selectedCount > 1 ? 's' : ''} selected
        </div>

        <div className="flex gap-2 flex-wrap">
          <motion.button
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.95 }}
            onClick={onApproveAll}
            className="px-4 py-2 bg-gradient-to-r from-green-500 to-green-600 hover:from-green-600 hover:to-green-700 text-white rounded-lg font-medium shadow-lg text-sm"
          >
            ✅ Approve All
          </motion.button>

          <motion.button
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.95 }}
            onClick={onRejectAll}
            className="px-4 py-2 bg-gradient-to-r from-red-500 to-red-600 hover:from-red-600 hover:to-red-700 text-white rounded-lg font-medium shadow-lg text-sm"
          >
            ❌ Reject All
          </motion.button>

          <motion.button
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.95 }}
            onClick={onExport}
            className={`px-4 py-2 rounded-lg font-medium shadow-lg text-sm ${
              darkMode
                ? 'bg-blue-600 hover:bg-blue-500 text-white'
                : 'bg-blue-500 hover:bg-blue-600 text-white'
            }`}
          >
            💾 Export YAML
          </motion.button>

          <motion.button
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.95 }}
            onClick={onClearSelection}
            className={`px-4 py-2 rounded-lg font-medium text-sm ${
              darkMode
                ? 'bg-gray-700 hover:bg-gray-600 text-white'
                : 'bg-gray-200 hover:bg-gray-300 text-gray-900'
            }`}
          >
            Clear
          </motion.button>
        </div>
      </div>
    </motion.div>
  );
};


/**
 * Confidence Meter Component
 * Visual indicator of AI confidence (0-100%)
 */

import React from 'react';
import { motion } from 'framer-motion';

interface ConfidenceMeterProps {
  confidence: number;
  darkMode?: boolean;
  showLabel?: boolean;
}

export const ConfidenceMeter: React.FC<ConfidenceMeterProps> = ({
  confidence,
  darkMode = false,
  showLabel = true
}) => {
  const percentage = Math.round(confidence * 100);
  
  const getColor = () => {
    if (confidence >= 0.9) return 'from-green-500 to-green-600';
    if (confidence >= 0.7) return 'from-yellow-500 to-yellow-600';
    return 'from-red-500 to-red-600';
  };

  const getLabel = () => {
    if (confidence >= 0.9) return 'High Confidence';
    if (confidence >= 0.7) return 'Medium Confidence';
    return 'Low Confidence';
  };

  return (
    <div>
      {showLabel && (
        <div className="flex justify-between items-center mb-2">
          <span className={`text-sm font-medium ${darkMode ? 'text-gray-300' : 'text-gray-700'}`}>
            {getLabel()}
          </span>
          <span className={`text-sm font-bold ${darkMode ? 'text-white' : 'text-gray-900'}`}>
            {percentage}%
          </span>
        </div>
      )}
      
      <div className={`w-full h-3 rounded-full overflow-hidden ${darkMode ? 'bg-gray-700' : 'bg-gray-200'}`}>
        <motion.div
          initial={{ width: 0 }}
          animate={{ width: `${percentage}%` }}
          transition={{ duration: 0.8, ease: 'easeOut' }}
          className={`h-full bg-gradient-to-r ${getColor()} shadow-lg`}
        />
      </div>
    </div>
  );
};


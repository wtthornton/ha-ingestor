/**
 * Settings Page
 * Configure AI automation preferences
 */

import React from 'react';
import { motion } from 'framer-motion';
import { useAppStore } from '../store';

export const Settings: React.FC = () => {
  const { darkMode } = useAppStore();

  return (
    <div className="space-y-6">
      <motion.div
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
      >
        <h1 className={`text-3xl font-bold mb-2 ${darkMode ? 'text-white' : 'text-gray-900'}`}>
          ⚙️ Settings
        </h1>
        <p className={darkMode ? 'text-gray-400' : 'text-gray-600'}>
          Configure your AI automation preferences
        </p>
      </motion.div>

      <div className={`rounded-xl p-8 ${darkMode ? 'bg-gray-800' : 'bg-white'} shadow-lg`}>
        <div className="text-center py-12">
          <div className="text-6xl mb-4">🚧</div>
          <h3 className={`text-xl font-bold mb-2 ${darkMode ? 'text-white' : 'text-gray-900'}`}>
            Settings Coming Soon
          </h3>
          <p className={darkMode ? 'text-gray-400' : 'text-gray-600'}>
            Configuration options will be added in future updates
          </p>

          <div className={`mt-8 text-left max-w-md mx-auto space-y-3 text-sm ${darkMode ? 'text-gray-400' : 'text-gray-600'}`}>
            <div>• Analysis schedule configuration</div>
            <div>• Confidence threshold settings</div>
            <div>• Category preferences</div>
            <div>• Budget management</div>
            <div>• Notification preferences</div>
          </div>
        </div>
      </div>
    </div>
  );
};


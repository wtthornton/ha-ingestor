/**
 * Batch Action Confirmation Modal
 * Modal dialog for confirming batch operations with progress tracking
 */

import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';

interface BatchActionModalProps {
  isOpen: boolean;
  onClose: () => void;
  onConfirm: () => Promise<void>;
  title: string;
  message: string;
  confirmLabel?: string;
  cancelLabel?: string;
  variant?: 'approve' | 'reject' | 'delete' | 'default';
  selectedCount: number;
  darkMode?: boolean;
}

export const BatchActionModal: React.FC<BatchActionModalProps> = ({
  isOpen,
  onClose,
  onConfirm,
  title,
  message,
  confirmLabel = 'Confirm',
  cancelLabel = 'Cancel',
  variant = 'default',
  selectedCount,
  darkMode = false
}) => {
  const [isProcessing, setIsProcessing] = useState(false);
  const [progress, setProgress] = useState(0);
  const [error, setError] = useState<string | null>(null);

  // Reset state when modal opens/closes
  useEffect(() => {
    if (!isOpen) {
      setIsProcessing(false);
      setProgress(0);
      setError(null);
    }
  }, [isOpen]);

  const handleConfirm = async () => {
    setIsProcessing(true);
    setError(null);
    setProgress(0);

    try {
      // Simulate progress for better UX
      const progressInterval = setInterval(() => {
        setProgress(prev => Math.min(prev + 10, 90));
      }, 100);

      await onConfirm();
      
      clearInterval(progressInterval);
      setProgress(100);
      
      // Wait a moment to show 100% before closing
      setTimeout(() => {
        onClose();
      }, 500);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Operation failed');
      setProgress(0);
    } finally {
      setIsProcessing(false);
    }
  };

  const getVariantColors = () => {
    switch (variant) {
      case 'approve':
        return {
          button: 'bg-gradient-to-r from-green-500 to-green-600 hover:from-green-600 hover:to-green-700',
          icon: '✅',
          accent: 'text-green-600'
        };
      case 'reject':
        return {
          button: 'bg-gradient-to-r from-red-500 to-red-600 hover:from-red-600 hover:to-red-700',
          icon: '❌',
          accent: 'text-red-600'
        };
      case 'delete':
        return {
          button: 'bg-gradient-to-r from-red-600 to-red-700 hover:from-red-700 hover:to-red-800',
          icon: '🗑️',
          accent: 'text-red-700'
        };
      default:
        return {
          button: 'bg-gradient-to-r from-blue-500 to-blue-600 hover:from-blue-600 hover:to-blue-700',
          icon: 'ℹ️',
          accent: 'text-blue-600'
        };
    }
  };

  const colors = getVariantColors();

  if (!isOpen) return null;

  return (
    <AnimatePresence>
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        exit={{ opacity: 0 }}
        className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50 backdrop-blur-sm"
        onClick={onClose}
      >
        <motion.div
          initial={{ scale: 0.9, opacity: 0, y: 20 }}
          animate={{ scale: 1, opacity: 1, y: 0 }}
          exit={{ scale: 0.9, opacity: 0, y: 20 }}
          transition={{ type: 'spring', damping: 25, stiffness: 300 }}
          className={`relative max-w-md w-full rounded-2xl shadow-2xl p-6 ${
            darkMode ? 'bg-gray-800 text-white' : 'bg-white text-gray-900'
          }`}
          onClick={(e) => e.stopPropagation()}
        >
          {/* Header */}
          <div className="flex items-start gap-4 mb-6">
            <div className={`text-4xl ${colors.accent}`}>
              {colors.icon}
            </div>
            <div className="flex-1">
              <h2 className={`text-2xl font-bold mb-2 ${darkMode ? 'text-white' : 'text-gray-900'}`}>
                {title}
              </h2>
              <p className={`text-sm ${darkMode ? 'text-gray-300' : 'text-gray-600'}`}>
                {message}
              </p>
              <div className={`mt-2 text-sm font-medium ${colors.accent}`}>
                {selectedCount} item{selectedCount > 1 ? 's' : ''} selected
              </div>
            </div>
          </div>

          {/* Progress Bar */}
          {isProcessing && (
            <div className="mb-6">
              <div className={`w-full h-2 rounded-full overflow-hidden ${
                darkMode ? 'bg-gray-700' : 'bg-gray-200'
              }`}>
                <motion.div
                  initial={{ width: 0 }}
                  animate={{ width: `${progress}%` }}
                  transition={{ duration: 0.3 }}
                  className={`h-full ${colors.button}`}
                />
              </div>
              <div className={`text-xs mt-2 text-center ${
                darkMode ? 'text-gray-400' : 'text-gray-500'
              }`}>
                Processing... {progress}%
              </div>
            </div>
          )}

          {/* Error Message */}
          {error && (
            <motion.div
              initial={{ opacity: 0, y: -10 }}
              animate={{ opacity: 1, y: 0 }}
              className="mb-6 p-4 rounded-lg bg-red-100 dark:bg-red-900/30 border-2 border-red-400 dark:border-red-600 text-red-800 dark:text-red-200"
            >
              <div className="flex items-center gap-2">
                <span className="text-xl">⚠️</span>
                <div>
                  <div className="font-semibold">Error</div>
                  <div className="text-sm">{error}</div>
                </div>
              </div>
            </motion.div>
          )}

          {/* Action Buttons */}
          <div className="flex gap-3">
            <button
              onClick={onClose}
              disabled={isProcessing}
              className={`flex-1 px-6 py-3 rounded-xl font-semibold transition-all ${
                darkMode
                  ? 'bg-gray-700 hover:bg-gray-600 text-white'
                  : 'bg-gray-200 hover:bg-gray-300 text-gray-900'
              } disabled:opacity-50 disabled:cursor-not-allowed`}
            >
              {cancelLabel}
            </button>
            <button
              onClick={handleConfirm}
              disabled={isProcessing}
              className={`flex-1 px-6 py-3 rounded-xl font-semibold text-white shadow-lg transition-all ${
                colors.button
              } disabled:opacity-50 disabled:cursor-not-allowed`}
            >
              {isProcessing ? (
                <span className="flex items-center justify-center gap-2">
                  <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
                  Processing...
                </span>
              ) : (
                confirmLabel
              )}
            </button>
          </div>

          {/* Keyboard Hint */}
          {!isProcessing && (
            <div className={`mt-4 text-xs text-center ${
              darkMode ? 'text-gray-500' : 'text-gray-400'
            }`}>
              Press Escape to cancel, Enter to confirm
            </div>
          )}
        </motion.div>
      </motion.div>
    </AnimatePresence>
  );
};

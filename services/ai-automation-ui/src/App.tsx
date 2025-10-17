/**
 * Main App Component
 * Routes and layout for AI Automation UI
 */

import React, { useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { Toaster } from 'react-hot-toast';
import { SelectionProvider } from './context/SelectionContext';
import { Navigation } from './components/Navigation';
import { Dashboard } from './pages/Dashboard';
import { Patterns } from './pages/Patterns';
import { Deployed } from './pages/Deployed';
import { Settings } from './pages/Settings';
import { useAppStore } from './store';

export const App: React.FC = () => {
  const { darkMode } = useAppStore();

  // Apply dark mode class to document
  useEffect(() => {
    if (darkMode) {
      document.documentElement.classList.add('dark');
    } else {
      document.documentElement.classList.remove('dark');
    }
  }, [darkMode]);

  return (
    <SelectionProvider>
      <Router>
        <div className={`min-h-screen transition-colors ${darkMode ? 'bg-gray-900' : 'bg-gray-50'}`}>
          <Navigation />
        
        <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/patterns" element={<Patterns />} />
            <Route path="/deployed" element={<Deployed />} />
            <Route path="/settings" element={<Settings />} />
          </Routes>
        </main>

        {/* Footer */}
        <footer className={`mt-16 py-8 border-t ${darkMode ? 'border-gray-800 bg-gray-900' : 'border-gray-200 bg-white'}`}>
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div className={`text-center text-sm ${darkMode ? 'text-gray-400' : 'text-gray-600'}`}>
              <div className="mb-2">
                <strong>HA AutomateAI</strong> - AI-Powered Smart Home Automation
              </div>
              <div className="text-xs">
                Powered by OpenAI GPT-4o-mini • Machine Learning Pattern Detection • Cost: ~$0.075/month
              </div>
              <div className="mt-4 flex justify-center gap-4">
                <a href="http://localhost:3000" target="_blank" rel="noopener noreferrer" className="hover:text-blue-500 transition-colors">
                  🔧 Admin Dashboard
                </a>
                <a href="http://localhost:8018/docs" target="_blank" rel="noopener noreferrer" className="hover:text-blue-500 transition-colors">
                  📚 API Docs
                </a>
              </div>
            </div>
          </div>
        </footer>

        {/* Toast Notifications */}
        <Toaster
          position="top-right"
          toastOptions={{
            duration: 4000,
            style: {
              background: darkMode ? '#374151' : '#fff',
              color: darkMode ? '#f3f4f6' : '#1f2937',
              border: `1px solid ${darkMode ? '#4b5563' : '#e5e7eb'}`,
              borderRadius: '12px',
              boxShadow: '0 10px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04)',
            },
            success: {
              iconTheme: {
                primary: '#10b981',
                secondary: '#fff',
              },
            },
            error: {
              iconTheme: {
                primary: '#ef4444',
                secondary: '#fff',
              },
            },
            loading: {
              iconTheme: {
                primary: '#3b82f6',
                secondary: '#fff',
              },
            },
          }}
        />
        </div>
      </Router>
    </SelectionProvider>
  );
};

export default App;


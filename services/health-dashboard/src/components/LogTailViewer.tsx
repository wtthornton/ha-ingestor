/**
 * LogTailViewer Component
 * 
 * Real-time log tail viewer with filtering and search
 * Epic 15.2: Live Event Stream & Log Viewer
 */

import React, { useState, useEffect, useRef } from 'react';

interface LogEntry {
  id: string;
  timestamp: string;
  level: 'DEBUG' | 'INFO' | 'WARNING' | 'ERROR' | 'CRITICAL';
  service: string;
  message: string;
  context?: any;
}

interface LogTailViewerProps {
  darkMode: boolean;
}

export const LogTailViewer: React.FC<LogTailViewerProps> = ({ darkMode }) => {
  const [logs, setLogs] = useState<LogEntry[]>([]);
  const [isPaused, setIsPaused] = useState(false);
  const [autoScroll, setAutoScroll] = useState(true);
  const [selectedLevel, setSelectedLevel] = useState<string>('all');
  const [selectedService, setSelectedService] = useState<string>('all');
  const [searchQuery, setSearchQuery] = useState('');
  
  const logsEndRef = useRef<HTMLDivElement>(null);
  const wsRef = useRef<WebSocket | null>(null);

  // WebSocket connection for logs
  useEffect(() => {
    const connectLogStream = () => {
      const ws = new WebSocket('ws://localhost:8003/ws/logs');
      
      ws.onopen = () => {
        console.log('Log stream connected');
      };
      
      ws.onmessage = (event) => {
        if (isPaused) return;
        
        try {
          const logEntry = JSON.parse(event.data);
          setLogs(prev => {
            // Keep max 1000 logs
            const updated = [logEntry, ...prev].slice(0, 1000);
            return updated;
          });
        } catch (e) {
          console.error('Failed to parse log entry:', e);
        }
      };
      
      ws.onerror = (error) => {
        console.error('Log stream error:', error);
      };
      
      ws.onclose = () => {
        console.log('Log stream disconnected');
        // Attempt reconnect after 5 seconds
        setTimeout(connectLogStream, 5000);
      };
      
      wsRef.current = ws;
    };
    
    connectLogStream();
    
    return () => {
      if (wsRef.current) {
        wsRef.current.close();
      }
    };
  }, [isPaused]);

  // Auto-scroll
  useEffect(() => {
    if (autoScroll && logsEndRef.current) {
      logsEndRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [logs, autoScroll]);

  // Filter logs
  const filteredLogs = logs.filter(log => {
    if (selectedLevel !== 'all' && log.level !== selectedLevel) return false;
    if (selectedService !== 'all' && log.service !== selectedService) return false;
    if (searchQuery && !log.message.toLowerCase().includes(searchQuery.toLowerCase())) return false;
    return true;
  });

  // Get unique services
  const services = ['all', ...Array.from(new Set(logs.map(l => l.service)))];

  // Get log level color
  const getLogLevelColor = (level: string) => {
    switch (level) {
      case 'CRITICAL':
      case 'ERROR':
        return darkMode ? 'text-red-400 bg-red-900/30' : 'text-red-700 bg-red-50';
      case 'WARNING':
        return darkMode ? 'text-yellow-400 bg-yellow-900/30' : 'text-yellow-700 bg-yellow-50';
      case 'INFO':
        return darkMode ? 'text-blue-400 bg-blue-900/30' : 'text-blue-700 bg-blue-50';
      case 'DEBUG':
        return darkMode ? 'text-gray-400 bg-gray-700' : 'text-gray-600 bg-gray-100';
      default:
        return darkMode ? 'text-gray-300' : 'text-gray-700';
    }
  };

  // Copy log to clipboard
  const copyLog = (log: LogEntry) => {
    const logText = `[${log.timestamp}] [${log.level}] [${log.service}] ${log.message}`;
    navigator.clipboard.writeText(logText);
  };

  // Clear logs
  const clearLogs = () => {
    setLogs([]);
  };

  return (
    <div className="space-y-4">
      {/* Controls */}
      <div className={`card-base p-4`}>
        <div className="flex flex-col sm:flex-row gap-4 items-start sm:items-center justify-between">
          <h2 className={`text-h2 ${darkMode ? 'text-white' : 'text-gray-900'}`}>
            📜 Live Log Viewer
          </h2>
          
          <div className="flex flex-wrap gap-2 w-full sm:w-auto">
            <button
              onClick={() => setIsPaused(!isPaused)}
              className={`btn-${isPaused ? 'success' : 'secondary'} text-sm min-h-[44px]`}
            >
              {isPaused ? '▶️ Resume' : '⏸️ Pause'}
            </button>
            
            <button
              onClick={() => setAutoScroll(!autoScroll)}
              className={`btn-${autoScroll ? 'primary' : 'secondary'} text-sm min-h-[44px]`}
            >
              {autoScroll ? '⬇️ Auto-scroll' : '⬇️ Scroll: OFF'}
            </button>
            
            <button
              onClick={clearLogs}
              className="btn-danger text-sm min-h-[44px]"
            >
              🗑️ Clear
            </button>
          </div>
        </div>
        
        {/* Filters */}
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 mt-4">
          <select
            value={selectedLevel}
            onChange={(e) => setSelectedLevel(e.target.value)}
            className="input-base min-h-[44px]"
          >
            <option value="all">All Levels</option>
            <option value="CRITICAL">Critical</option>
            <option value="ERROR">Error</option>
            <option value="WARNING">Warning</option>
            <option value="INFO">Info</option>
            <option value="DEBUG">Debug</option>
          </select>
          
          <select
            value={selectedService}
            onChange={(e) => setSelectedService(e.target.value)}
            className="input-base min-h-[44px]"
          >
            {services.map(service => (
              <option key={service} value={service}>
                {service === 'all' ? 'All Services' : service}
              </option>
            ))}
          </select>
          
          <input
            type="text"
            placeholder="Search logs..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="input-base min-h-[44px]"
          />
        </div>
        
        <div className="flex gap-4 mt-3 text-sm">
          <span className={`${darkMode ? 'text-gray-400' : 'text-gray-600'}`}>
            Total: <span className="font-semibold">{logs.length}</span>
          </span>
          <span className={`${darkMode ? 'text-gray-400' : 'text-gray-600'}`}>
            Filtered: <span className="font-semibold">{filteredLogs.length}</span>
          </span>
          <span className={`${darkMode ? 'text-gray-400' : 'text-gray-600'}`}>
            Status: <span className="font-semibold">{isPaused ? 'Paused' : 'Live'}</span>
          </span>
        </div>
      </div>
      
      {/* Log List */}
      <div className={`card-base p-3 max-h-[600px] overflow-y-auto font-mono text-xs`}>
        {filteredLogs.length === 0 ? (
          <div className="text-center py-12">
            <p className={`${darkMode ? 'text-gray-400' : 'text-gray-500'}`}>
              {isPaused ? '⏸️ Log stream paused' : '⏳ Waiting for logs...'}
            </p>
          </div>
        ) : (
          <div className="space-y-1">
            {filteredLogs.map((log, index) => (
              <div
                key={log.id}
                style={{ animationDelay: `${Math.min(index * 0.01, 0.5)}s` }}
                className={`flex items-start gap-2 p-2 rounded hover:bg-gray-100 dark:hover:bg-gray-700 cursor-pointer transition-colors content-fade-in`}
                onClick={() => copyLog(log)}
                title="Click to copy"
              >
                <span className={`badge-base ${getLogLevelColor(log.level)} px-2 py-0.5 flex-shrink-0`}>
                  {log.level}
                </span>
                <span className={`${darkMode ? 'text-gray-400' : 'text-gray-500'} flex-shrink-0`}>
                  {new Date(log.timestamp).toLocaleTimeString()}
                </span>
                <span className={`${darkMode ? 'text-gray-500' : 'text-gray-400'} flex-shrink-0`}>
                  [{log.service}]
                </span>
                <span className={`${darkMode ? 'text-gray-300' : 'text-gray-700'} break-all`}>
                  {log.message}
                </span>
              </div>
            ))}
            <div ref={logsEndRef} />
          </div>
        )}
      </div>
    </div>
  );
};


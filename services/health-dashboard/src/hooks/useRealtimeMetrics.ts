/**
 * useRealtimeMetrics Hook
 * 
 * Real-time WebSocket connection for dashboard metrics with automatic fallback to HTTP polling
 * Epic 15.1: Real-Time WebSocket Integration
 * 
 * Features:
 * - WebSocket connection with auto-reconnect (exponential backoff)
 * - Automatic fallback to HTTP polling if WebSocket fails
 * - Heartbeat/ping support for connection health
 * - Connection status tracking
 * - Type-safe message handling
 */

import { useEffect, useState, useCallback, useRef } from 'react';
import useWebSocket, { ReadyState } from 'react-use-websocket';

export interface RealtimeMetrics {
  health: any;
  statistics: any;
  events: any[];
  timestamp: string;
}

export interface WebSocketMessage {
  type: 'initial_data' | 'health_update' | 'stats_update' | 'events_update' | 'pong' | 'error';
  data?: any;
  message?: string;
  timestamp: string;
}

export interface UseRealtimeMetricsOptions {
  enabled?: boolean;
  pollingInterval?: number; // Fallback polling interval in ms
  heartbeatInterval?: number; // Heartbeat interval in ms
  onConnectionChange?: (connected: boolean) => void;
}

export interface UseRealtimeMetricsReturn {
  metrics: RealtimeMetrics | null;
  isConnected: boolean;
  connectionState: 'connecting' | 'connected' | 'disconnected' | 'error' | 'fallback';
  error: string | null;
  sendMessage: (message: any) => void;
  reconnect: () => void;
}

const WS_URL = import.meta.env.VITE_WS_URL || 'ws://localhost:8003/ws';
const HTTP_HEALTH_URL = '/api/health';
const HTTP_STATS_URL = '/api/statistics';

export const useRealtimeMetrics = (
  options: UseRealtimeMetricsOptions = {}
): UseRealtimeMetricsReturn => {
  const {
    enabled = true,
    pollingInterval = 30000,
    heartbeatInterval = 25000,
    onConnectionChange
  } = options;

  const [metrics, setMetrics] = useState<RealtimeMetrics | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isFallbackMode, setIsFallbackMode] = useState(false);
  const fallbackTimerRef = useRef<NodeJS.Timeout | null>(null);
  const heartbeatTimerRef = useRef<NodeJS.Timeout | null>(null);
  const reconnectAttemptsRef = useRef(0);

  // WebSocket connection with exponential backoff
  const {
    sendMessage: wsSendMessage,
    sendJsonMessage,
    lastMessage,
    lastJsonMessage,
    readyState,
    getWebSocket
  } = useWebSocket(
    WS_URL,
    {
      shouldReconnect: () => enabled && !isFallbackMode,
      reconnectAttempts: 10,
      reconnectInterval: (attemptNumber) => {
        // Exponential backoff: 1s, 2s, 4s, 8s, max 10s
        reconnectAttemptsRef.current = attemptNumber;
        return Math.min(Math.pow(2, attemptNumber) * 1000, 10000);
      },
      onOpen: () => {
        console.log('WebSocket connected');
        setError(null);
        setIsFallbackMode(false);
        reconnectAttemptsRef.current = 0;
        onConnectionChange?.(true);
        
        // Start heartbeat
        startHeartbeat();
      },
      onClose: (event) => {
        console.log('WebSocket closed:', event.code, event.reason);
        onConnectionChange?.(false);
        stopHeartbeat();
        
        // If closed and reconnect failed, fallback to polling
        if (reconnectAttemptsRef.current >= 10) {
          console.log('WebSocket reconnect failed, falling back to HTTP polling');
          setIsFallbackMode(true);
          startHttpPolling();
        }
      },
      onError: (event) => {
        console.error('WebSocket error:', event);
        setError('WebSocket connection error');
      },
      onMessage: (event) => {
        try {
          const message: WebSocketMessage = JSON.parse(event.data);
          handleWebSocketMessage(message);
        } catch (e) {
          console.error('Failed to parse WebSocket message:', e);
        }
      },
      heartbeat: {
        message: 'ping',
        returnMessage: 'pong',
        timeout: 60000, // 1 minute timeout
        interval: heartbeatInterval, // 25 seconds
      },
      retryOnError: true,
    },
    enabled && !isFallbackMode
  );

  // Handle WebSocket messages
  const handleWebSocketMessage = useCallback((message: WebSocketMessage) => {
    switch (message.type) {
      case 'initial_data':
        setMetrics({
          health: message.data.health,
          statistics: message.data.statistics,
          events: message.data.events || [],
          timestamp: message.timestamp
        });
        break;
      
      case 'health_update':
        setMetrics(prev => prev ? {
          ...prev,
          health: message.data,
          timestamp: message.timestamp
        } : null);
        break;
      
      case 'stats_update':
        setMetrics(prev => prev ? {
          ...prev,
          statistics: message.data,
          timestamp: message.timestamp
        } : null);
        break;
      
      case 'events_update':
        setMetrics(prev => prev ? {
          ...prev,
          events: message.data || [],
          timestamp: message.timestamp
        } : null);
        break;
      
      case 'error':
        setError(message.message || 'Unknown error');
        break;
      
      case 'pong':
        // Heartbeat response received
        break;
    }
  }, []);

  // Heartbeat management
  const startHeartbeat = useCallback(() => {
    stopHeartbeat();
    heartbeatTimerRef.current = setInterval(() => {
      if (readyState === ReadyState.OPEN) {
        sendJsonMessage({ type: 'ping', timestamp: new Date().toISOString() });
      }
    }, heartbeatInterval);
  }, [readyState, sendJsonMessage, heartbeatInterval]);

  const stopHeartbeat = useCallback(() => {
    if (heartbeatTimerRef.current) {
      clearInterval(heartbeatTimerRef.current);
      heartbeatTimerRef.current = null;
    }
  }, []);

  // HTTP polling fallback
  const startHttpPolling = useCallback(() => {
    stopHttpPolling();
    
    const fetchData = async () => {
      try {
        const [healthRes, statsRes] = await Promise.all([
          fetch(HTTP_HEALTH_URL),
          fetch(HTTP_STATS_URL)
        ]);

        if (healthRes.ok && statsRes.ok) {
          const health = await healthRes.json();
          const statistics = await statsRes.json();
          
          setMetrics({
            health,
            statistics,
            events: [],
            timestamp: new Date().toISOString()
          });
          setError(null);
        }
      } catch (e) {
        console.error('HTTP polling error:', e);
        setError('Failed to fetch data');
      }
    };

    // Initial fetch
    fetchData();
    
    // Set up polling
    fallbackTimerRef.current = setInterval(fetchData, pollingInterval);
  }, [pollingInterval]);

  const stopHttpPolling = useCallback(() => {
    if (fallbackTimerRef.current) {
      clearInterval(fallbackTimerRef.current);
      fallbackTimerRef.current = null;
    }
  }, []);

  // Manual reconnect
  const reconnect = useCallback(() => {
    console.log('Manual reconnect triggered');
    setIsFallbackMode(false);
    reconnectAttemptsRef.current = 0;
    stopHttpPolling();
    
    // Force reconnect by getting the WebSocket instance
    const ws = getWebSocket();
    if (ws && ws.readyState !== WebSocket.OPEN) {
      ws.close();
    }
  }, [getWebSocket]);

  // Send custom message
  const sendMessage = useCallback((message: any) => {
    if (readyState === ReadyState.OPEN) {
      sendJsonMessage(message);
    } else {
      console.warn('Cannot send message: WebSocket not connected');
    }
  }, [readyState, sendJsonMessage]);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      stopHeartbeat();
      stopHttpPolling();
    };
  }, [stopHeartbeat, stopHttpPolling]);

  // Determine connection state
  const getConnectionState = (): 'connecting' | 'connected' | 'disconnected' | 'error' | 'fallback' => {
    if (isFallbackMode) return 'fallback';
    if (error) return 'error';
    
    switch (readyState) {
      case ReadyState.CONNECTING:
        return 'connecting';
      case ReadyState.OPEN:
        return 'connected';
      case ReadyState.CLOSING:
      case ReadyState.CLOSED:
        return 'disconnected';
      default:
        return 'disconnected';
    }
  };

  return {
    metrics,
    isConnected: readyState === ReadyState.OPEN,
    connectionState: getConnectionState(),
    error,
    sendMessage,
    reconnect
  };
};


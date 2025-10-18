/**
 * Enhanced Alert Banner Component
 * Epic 17.4: Critical Alerting System
 * 
 * Displays active critical alerts with enhanced user information:
 * - Clear explanations of what each alert means
 * - Actionable steps for resolution
 * - Historical context and current status
 * - Better visual indicators for resolved vs active issues
 */

import React, { useState, useEffect } from 'react';
import { apiService } from '../services/api';

export enum AlertSeverity {
  INFO = 'info',
  WARNING = 'warning',
  CRITICAL = 'critical'
}

export enum AlertStatus {
  ACTIVE = 'active',
  RESOLVED = 'resolved',
  ACKNOWLEDGED = 'acknowledged'
}

export interface Alert {
  id: string;
  name: string;
  severity: AlertSeverity;
  status: AlertStatus;
  message: string;
  service: string;
  metric?: string;
  current_value?: number;
  threshold_value?: number;
  created_at?: string;
  resolved_at?: string;
  acknowledged_at?: string;
  metadata?: Record<string, any>;
}

interface AlertBannerProps {
  darkMode: boolean;
}

export const AlertBanner: React.FC<AlertBannerProps> = ({ darkMode }) => {
  const [alerts, setAlerts] = useState<Alert[]>([]);
  const [loading, setLoading] = useState(true);

  // Fetch active alerts
  useEffect(() => {
    const fetchAlerts = async () => {
      try {
        const response = await fetch('http://localhost:8003/api/v1/alerts/active');
        if (response.ok) {
          const data = await response.json();
          setAlerts(data);
        }
        setLoading(false);
      } catch (error) {
        console.error('Failed to fetch alerts:', error);
        setLoading(false);
      }
    };

    fetchAlerts();
    const interval = setInterval(fetchAlerts, 10000); // Refresh every 10s

    return () => clearInterval(interval);
  }, []);

  // Handle alert acknowledgment
  const acknowledgeAlert = async (alertId: string) => {
    try {
      const response = await fetch(`http://localhost:8003/api/v1/alerts/${alertId}/acknowledge`, {
        method: 'POST'
      });
      
      if (response.ok) {
        setAlerts(prev => prev.filter(a => a.id !== alertId));
      }
    } catch (error) {
      console.error('Failed to acknowledge alert:', error);
    }
  };

  // Handle alert resolution
  const resolveAlert = async (alertId: string) => {
    try {
      const response = await fetch(`http://localhost:8003/api/v1/alerts/${alertId}/resolve`, {
        method: 'POST'
      });
      
      if (response.ok) {
        setAlerts(prev => prev.filter(a => a.id !== alertId));
      }
    } catch (error) {
      console.error('Failed to resolve alert:', error);
    }
  };

  // Get severity styling
  const getSeverityStyle = (severity: AlertSeverity): string => {
    const styles = {
      [AlertSeverity.CRITICAL]: darkMode 
        ? 'bg-red-900/50 border-red-500 text-red-200' 
        : 'bg-red-50 border-red-500 text-red-900',
      [AlertSeverity.WARNING]: darkMode 
        ? 'bg-yellow-900/50 border-yellow-500 text-yellow-200' 
        : 'bg-yellow-50 border-yellow-500 text-yellow-900',
      [AlertSeverity.INFO]: darkMode 
        ? 'bg-blue-900/50 border-blue-500 text-blue-200' 
        : 'bg-blue-50 border-blue-500 text-blue-900'
    };
    
    return styles[severity] || styles[AlertSeverity.INFO];
  };

  // Get severity icon
  const getSeverityIcon = (severity: AlertSeverity): string => {
    const icons = {
      [AlertSeverity.CRITICAL]: '🚨',
      [AlertSeverity.WARNING]: '⚠️',
      [AlertSeverity.INFO]: 'ℹ️'
    };
    
    return icons[severity] || 'ℹ️';
  };

  // Get enhanced alert information
  const getAlertInfo = (alert: Alert) => {
    const now = new Date();
    const alertTime = alert.created_at ? new Date(alert.created_at) : now;
    const timeDiff = now.getTime() - alertTime.getTime();
    const hoursAgo = Math.floor(timeDiff / (1000 * 60 * 60));
    const minutesAgo = Math.floor(timeDiff / (1000 * 60));

    // Determine if this is a historical alert (service is now healthy)
    const isHistorical = alert.metadata?.message?.includes('Timeout') && 
                        alert.metadata?.response_time_ms >= 2000;

    return {
      timeAgo: hoursAgo > 0 ? `${hoursAgo}h ago` : `${minutesAgo}m ago`,
      isHistorical,
      explanation: getAlertExplanation(alert),
      actionSteps: getActionSteps(alert),
      currentStatus: getCurrentStatus(alert)
    };
  };

  // Get clear explanation of what the alert means
  const getAlertExplanation = (alert: Alert): string => {
    if (alert.name === 'service_unhealthy' && alert.metadata?.message?.includes('Timeout')) {
      return `The ${alert.service} service experienced connection timeouts to its dependencies. This typically indicates network issues or service overload.`;
    }
    
    if (alert.metric === 'health_status') {
      return `The ${alert.service} service reported an unhealthy status, indicating it may not be functioning properly.`;
    }

    return `The ${alert.service} service has reported an issue with ${alert.metric || 'its status'}.`;
  };

  // Get actionable steps for resolution
  const getActionSteps = (alert: Alert): string[] => {
    const steps = [];
    
    if (alert.name === 'service_unhealthy' && alert.metadata?.message?.includes('Timeout')) {
      steps.push('Check if the service is currently responding normally');
      steps.push('Verify network connectivity between services');
      steps.push('Review service logs for any ongoing issues');
      steps.push('If resolved, click "Resolve" to clear this historical alert');
    } else {
      steps.push('Check the service status and logs');
      steps.push('Verify all dependencies are healthy');
      steps.push('Restart the service if necessary');
    }
    
    return steps;
  };

  // Get current status assessment
  const getCurrentStatus = (alert: Alert): { status: string; color: string } => {
    const now = new Date();
    const alertTime = alert.created_at ? new Date(alert.created_at) : now;
    const timeDiff = now.getTime() - alertTime.getTime();
    const hoursAgo = Math.floor(timeDiff / (1000 * 60 * 60));

    if (alert.metadata?.message?.includes('Timeout') && hoursAgo > 1) {
      return { 
        status: 'Likely Resolved - Historical Alert', 
        color: darkMode ? 'text-yellow-300' : 'text-yellow-600' 
      };
    }

    return { 
      status: 'Active Issue', 
      color: darkMode ? 'text-red-300' : 'text-red-600' 
    };
  };

  if (loading || alerts.length === 0) {
    return null;
  }

  return (
    <div className="space-y-3 mb-6">
      {alerts.map(alert => {
        const alertInfo = getAlertInfo(alert);
        
        return (
          <div
            key={alert.id}
            className={`border-l-4 p-5 rounded-lg ${getSeverityStyle(alert.severity)} shadow-sm ${
              alertInfo.isHistorical ? 'opacity-90' : ''
            }`}
            role="alert"
          >
            <div className="flex items-start justify-between gap-4">
              <div className="flex items-start gap-3 flex-1">
                <span className="text-2xl mt-0.5">{getSeverityIcon(alert.severity)}</span>
                
                <div className="flex-1">
                  {/* Header with service info */}
                  <div className="flex items-center gap-2 mb-2">
                    <span className="font-semibold text-sm uppercase tracking-wide">
                      {alert.severity}
                    </span>
                    <span className="text-xs opacity-75">•</span>
                    <span className="text-xs opacity-75 font-medium">
                      {alert.service}
                    </span>
                    {alert.metric && (
                      <>
                        <span className="text-xs opacity-75">•</span>
                        <span className="text-xs opacity-75 font-mono">
                          {alert.metric}
                        </span>
                      </>
                    )}
                    <span className="text-xs opacity-75">•</span>
                    <span className={`text-xs font-medium ${alertInfo.currentStatus.color}`}>
                      {alertInfo.currentStatus.status}
                    </span>
                  </div>
                  
                  {/* Enhanced explanation */}
                  <div className="mb-3">
                    <p className="font-medium mb-1">{alert.message}</p>
                    <p className="text-sm opacity-90 leading-relaxed">
                      {alertInfo.explanation}
                    </p>
                  </div>

                  {/* Action steps */}
                  <div className="mb-3">
                    <h4 className="text-sm font-semibold mb-2 opacity-90">What to do:</h4>
                    <ul className="text-sm space-y-1 opacity-80">
                      {alertInfo.actionSteps.map((step, index) => (
                        <li key={index} className="flex items-start gap-2">
                          <span className="text-xs mt-1">•</span>
                          <span>{step}</span>
                        </li>
                      ))}
                    </ul>
                  </div>
                  
                  {/* Timestamp and technical details */}
                  <div className="text-xs opacity-75 flex items-center gap-4 flex-wrap">
                    <span>
                      Triggered: {alert.created_at ? new Date(alert.created_at).toLocaleString() : 'Unknown'} ({alertInfo.timeAgo})
                    </span>
                    {alert.current_value !== undefined && (
                      <span>
                        Current: {(alert.current_value ?? 0).toFixed(1)}
                        {alert.threshold_value !== undefined && ` (threshold: ${alert.threshold_value})`}
                      </span>
                    )}
                    {alert.metadata?.response_time_ms && (
                      <span>
                        Response time: {alert.metadata.response_time_ms}ms
                      </span>
                    )}
                  </div>
                </div>
              </div>

              {/* Action buttons */}
              <div className="flex gap-2 flex-shrink-0">
                <button
                  onClick={() => acknowledgeAlert(alert.id)}
                  className={`px-3 py-1 text-xs rounded transition-colors min-h-[32px] ${
                    darkMode
                      ? 'bg-gray-700 hover:bg-gray-600 text-gray-200'
                      : 'bg-gray-200 hover:bg-gray-300 text-gray-700'
                  }`}
                  title="Acknowledge that you've seen this alert"
                >
                  ✓ Ack
                </button>
                
                <button
                  onClick={() => resolveAlert(alert.id)}
                  className={`px-3 py-1 text-xs rounded transition-colors min-h-[32px] ${
                    darkMode
                      ? 'bg-green-700 hover:bg-green-600 text-white'
                      : 'bg-green-100 hover:bg-green-200 text-green-700'
                  }`}
                  title="Mark this alert as resolved"
                >
                  ✓ Resolve
                </button>
              </div>
            </div>
          </div>
        );
      })}
    </div>
  );
};

export default AlertBanner;


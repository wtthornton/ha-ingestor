/**
 * API Service for AI Automation Backend
 * Connects to ai-automation-service on port 8018
 */

import type { Suggestion, Pattern, ScheduleInfo, AnalysisStatus, UsageStats } from '../types';

// Use relative path - nginx will proxy to ai-automation-service
// In production (Docker), nginx proxies /api to http://ai-automation-service:8018/api
// In development, use direct connection to localhost:8018
const API_BASE_URL = import.meta.env.VITE_API_URL || (
  import.meta.env.MODE === 'development' 
    ? 'http://localhost:8018/api' 
    : '/api'
);

class APIError extends Error {
  constructor(public status: number, message: string) {
    super(message);
    this.name = 'APIError';
  }
}

async function fetchJSON<T>(url: string, options?: RequestInit): Promise<T> {
  try {
    const response = await fetch(url, {
      ...options,
      headers: {
        'Content-Type': 'application/json',
        ...options?.headers,
      },
    });

    if (!response.ok) {
      throw new APIError(response.status, `API error: ${response.statusText}`);
    }

    return await response.json();
  } catch (error) {
    console.error(`API request failed: ${url}`, error);
    throw error;
  }
}

export const api = {
  // Suggestions
  async getSuggestions(status?: string, limit = 50): Promise<{ data: { suggestions: Suggestion[], count: number } }> {
    const params = new URLSearchParams();
    if (status) params.append('status', status);
    params.append('limit', limit.toString());
    
    return fetchJSON(`${API_BASE_URL}/suggestions/list?${params}`);
  },

  async approveSuggestion(id: number): Promise<any> {
    return fetchJSON(`${API_BASE_URL}/suggestions/${id}/approve`, {
      method: 'PATCH',
    });
  },

  async rejectSuggestion(id: number, reason?: string): Promise<any> {
    const body = reason ? { action: 'rejected', feedback_text: reason } : undefined;
    return fetchJSON(`${API_BASE_URL}/suggestions/${id}/reject`, {
      method: 'PATCH',
      body: body ? JSON.stringify(body) : undefined,
    });
  },

  async updateSuggestion(id: number, updates: any): Promise<any> {
    return fetchJSON(`${API_BASE_URL}/suggestions/${id}`, {
      method: 'PATCH',
      body: JSON.stringify(updates),
    });
  },

  async deleteSuggestion(id: number): Promise<any> {
    return fetchJSON(`${API_BASE_URL}/suggestions/${id}`, {
      method: 'DELETE',
    });
  },

  async batchApproveSuggestions(suggestionIds: number[]): Promise<any> {
    return fetchJSON(`${API_BASE_URL}/suggestions/batch/approve`, {
      method: 'POST',
      body: JSON.stringify(suggestionIds),
    });
  },

  async batchRejectSuggestions(suggestionIds: number[]): Promise<any> {
    return fetchJSON(`${API_BASE_URL}/suggestions/batch/reject`, {
      method: 'POST',
      body: JSON.stringify(suggestionIds),
    });
  },

  // Analysis
  async triggerAnalysis(params?: {
    days?: number;
    max_suggestions?: number;
    min_confidence?: number;
  }): Promise<any> {
    return fetchJSON(`${API_BASE_URL}/analysis/analyze-and-suggest`, {
      method: 'POST',
      body: JSON.stringify({
        days: params?.days || 30,
        max_suggestions: params?.max_suggestions || 10,
        min_confidence: params?.min_confidence || 0.7,
        time_of_day_enabled: true,
        co_occurrence_enabled: true,
      }),
    });
  },

  async triggerManualJob(): Promise<any> {
    return fetchJSON(`${API_BASE_URL}/analysis/trigger`, {
      method: 'POST',
    });
  },

  async getAnalysisStatus(): Promise<AnalysisStatus> {
    return fetchJSON(`${API_BASE_URL}/analysis/status`);
  },

  async getScheduleInfo(): Promise<ScheduleInfo> {
    return fetchJSON(`${API_BASE_URL}/analysis/schedule`);
  },

  // Patterns
  async getPatterns(type?: string, minConfidence?: number): Promise<{ data: { patterns: Pattern[], count: number } }> {
    const params = new URLSearchParams();
    if (type) params.append('pattern_type', type);
    if (minConfidence) params.append('min_confidence', minConfidence.toString());
    params.append('limit', '100');
    
    return fetchJSON(`${API_BASE_URL}/patterns/list?${params}`);
  },

  async getPatternStats(): Promise<any> {
    return fetchJSON(`${API_BASE_URL}/patterns/stats`);
  },

  // Usage & Cost
  async getUsageStats(): Promise<{ data: UsageStats }> {
    return fetchJSON(`${API_BASE_URL}/suggestions/usage-stats`);
  },

  async resetUsageStats(): Promise<any> {
    return fetchJSON(`${API_BASE_URL}/suggestions/usage-stats/reset`, {
      method: 'POST',
    });
  },

  // Deployment (Story AI1.11)
  async deploySuggestion(suggestionId: number): Promise<any> {
    return fetchJSON(`${API_BASE_URL}/deploy/${suggestionId}`, {
      method: 'POST',
    });
  },

  async batchDeploySuggestions(suggestionIds: number[]): Promise<any> {
    return fetchJSON(`${API_BASE_URL}/deploy/batch`, {
      method: 'POST',
      body: JSON.stringify(suggestionIds),
    });
  },

  async listDeployedAutomations(): Promise<any> {
    return fetchJSON(`${API_BASE_URL}/deploy/automations`);
  },

  async getAutomationStatus(automationId: string): Promise<any> {
    return fetchJSON(`${API_BASE_URL}/deploy/automations/${automationId}`);
  },

  async enableAutomation(automationId: string): Promise<any> {
    return fetchJSON(`${API_BASE_URL}/deploy/automations/${automationId}/enable`, {
      method: 'POST',
    });
  },

  async disableAutomation(automationId: string): Promise<any> {
    return fetchJSON(`${API_BASE_URL}/deploy/automations/${automationId}/disable`, {
      method: 'POST',
    });
  },

  async triggerAutomation(automationId: string): Promise<any> {
    return fetchJSON(`${API_BASE_URL}/deploy/automations/${automationId}/trigger`, {
      method: 'POST',
    });
  },

  async testHAConnection(): Promise<any> {
    return fetchJSON(`${API_BASE_URL}/deploy/test-connection`);
  },

  // Device name resolution
  async getDeviceName(deviceId: string): Promise<string> {
    try {
      // Handle compound entity IDs (e.g., "hash1+hash2")
      if (deviceId.includes('+')) {
        const parts = deviceId.split('+');
        if (parts.length === 2) {
          // This is a co-occurrence pattern with two entity hashes
          // Try to get more meaningful names by looking up patterns
          const patternInfo = await this.getPatternInfo(deviceId);
          if (patternInfo) {
            return patternInfo;
          }
          
          // Fallback to descriptive name
          return `Co-occurrence Pattern (${parts[0].substring(0, 8)}... + ${parts[1].substring(0, 8)}...)`;
        }
      }
      
      // Try to get device info from data API
      const response = await fetch(`http://localhost:8006/api/devices/${deviceId}`);
      if (response.ok) {
        const device = await response.json();
        return device.name || deviceId;
      }
    } catch (error) {
      console.warn(`Failed to resolve device name for ${deviceId}:`, error);
    }
    
    // Fallback: try to extract readable name from device ID
    // Some device IDs might have readable parts after splitting
    const parts = deviceId.split('.');
    if (parts.length > 1) {
      return parts[1] || deviceId;
    }
    
    // Last resort: return truncated device ID
    return deviceId.length > 20 ? `${deviceId.substring(0, 20)}...` : deviceId;
  },

  // Get pattern information for better naming
  async getPatternInfo(deviceId: string): Promise<string | null> {
    try {
      // Try to get pattern details from the AI automation service
      const response = await fetch(`${API_BASE_URL}/patterns/list?device_id=${encodeURIComponent(deviceId)}&limit=1`);
      if (response.ok) {
        const data = await response.json();
        const patterns = data.data?.patterns || [];
        if (patterns.length > 0) {
          const pattern = patterns[0];
          // Create a more meaningful name based on pattern type and metadata
          if (pattern.pattern_type === 'co_occurrence') {
            const occurrences = pattern.occurrences || 0;
            const confidence = Math.round(pattern.confidence || 0);
            return `Co-occurrence Pattern (${occurrences} occurrences, ${confidence}% confidence)`;
          } else if (pattern.pattern_type === 'time_of_day') {
            const hour = pattern.metadata?.hour || 0;
            const minute = pattern.metadata?.minute || 0;
            const occurrences = pattern.occurrences || 0;
            return `Time Pattern (${hour.toString().padStart(2, '0')}:${minute.toString().padStart(2, '0')}, ${occurrences} occurrences)`;
          }
        }
      }
    } catch (error) {
      console.warn(`Failed to get pattern info for ${deviceId}:`, error);
    }
    return null;
  },

  async getDeviceNames(deviceIds: string[]): Promise<Record<string, string>> {
    const nameMap: Record<string, string> = {};
    
    // Process in batches to avoid overwhelming the API
    const batchSize = 10;
    for (let i = 0; i < deviceIds.length; i += batchSize) {
      const batch = deviceIds.slice(i, i + batchSize);
      const promises = batch.map(async (deviceId) => {
        const name = await this.getDeviceName(deviceId);
        return { deviceId, name };
      });
      
      const results = await Promise.all(promises);
      results.forEach(({ deviceId, name }) => {
        nameMap[deviceId] = name;
      });
    }
    
    return nameMap;
  },
};

export default api;


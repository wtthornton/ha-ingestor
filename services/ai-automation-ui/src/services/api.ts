/**
 * API Service for AI Automation Backend
 * Connects to ai-automation-service on port 8018
 */

import type { Suggestion, Pattern, ScheduleInfo, AnalysisStatus, UsageStats } from '../types';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8018/api';

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
  async getSuggestions(status?: string, limit = 50): Promise<{ data: Suggestion[] }> {
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
  async getPatterns(type?: string, minConfidence?: number): Promise<{ data: Pattern[] }> {
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
};

export default api;


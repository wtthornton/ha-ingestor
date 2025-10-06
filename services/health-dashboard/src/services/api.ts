import { HealthStatus, Statistics } from '../types';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || '/api';

class ApiService {
  private async fetchWithErrorHandling<T>(url: string): Promise<T> {
    try {
      const response = await fetch(url);
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }
      return await response.json();
    } catch (error) {
      console.error(`API Error for ${url}:`, error);
      throw error;
    }
  }

  async getHealth(): Promise<HealthStatus> {
    // Simplified API returns data directly
    return this.fetchWithErrorHandling<HealthStatus>(`${API_BASE_URL}/health`);
  }

  async getStatistics(period: string = '1h'): Promise<Statistics> {
    // Simplified API returns data directly
    return this.fetchWithErrorHandling<Statistics>(`${API_BASE_URL}/stats?period=${period}`);
  }

  async getServicesHealth(): Promise<{ [key: string]: any }> {
    return this.fetchWithErrorHandling<{ [key: string]: any }>(`${API_BASE_URL}/health/services`);
  }
}

export const apiService = new ApiService();

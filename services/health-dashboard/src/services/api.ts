import { HealthStatus, Statistics, DataSourceHealth, DataSourceMetrics } from '../types';
import { ServiceHealthResponse } from '../types/health';

// Docker management types
export interface ContainerInfo {
  name: string;
  service_name: string;
  status: string;
  image: string;
  created: string;
  ports: Record<string, string>;
  is_project_container: boolean;
}

export interface ContainerOperationResponse {
  success: boolean;
  message: string;
  timestamp: string;
}

export interface ContainerStats {
  cpu_percent?: number;
  memory_usage?: number;
  memory_limit?: number;
  memory_percent?: number;
  timestamp: string;
}

export interface APIKeyInfo {
  service: string;
  key_name: string;
  status: string;
  masked_key: string;
  is_required: boolean;
  description: string;
}

export interface APIKeyUpdateRequest {
  api_key: string;
}

export interface APIKeyTestResponse {
  success: boolean;
  message: string;
  timestamp: string;
}

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || '/api';

class ApiService {
  private async fetchWithErrorHandling<T>(url: string, options?: RequestInit): Promise<T> {
    try {
      const response = await fetch(url, options);
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
    return this.fetchWithErrorHandling<HealthStatus>(`${API_BASE_URL}/health`);
  }

  async getEnhancedHealth(): Promise<ServiceHealthResponse> {
    return this.fetchWithErrorHandling<ServiceHealthResponse>(`${API_BASE_URL}/health`);
  }

  async getStatistics(period: string = '1h'): Promise<Statistics> {
    return this.fetchWithErrorHandling<Statistics>(`${API_BASE_URL}/stats?period=${period}`);
  }

  async getServicesHealth(): Promise<{ [key: string]: any }> {
    return this.fetchWithErrorHandling<{ [key: string]: any }>(`${API_BASE_URL}/health/services`);
  }

  // New data source health endpoints
  async getDataSourceHealth(port: number): Promise<DataSourceHealth> {
    try {
      return await fetch(`http://localhost:${port}/health`).then(r => r.json());
    } catch (error) {
      console.error(`Error fetching health from port ${port}:`, error);
      throw error;
    }
  }

  async getAllDataSources(): Promise<{
    carbonIntensity: DataSourceHealth;
    electricityPricing: DataSourceHealth;
    airQuality: DataSourceHealth;
    calendar: DataSourceHealth;
    smartMeter: DataSourceHealth;
  }> {
    // Only check optional services if they're configured to run
    // For now, return null for all optional services to avoid connection errors
    return {
      carbonIntensity: null,
      electricityPricing: null,
      airQuality: null,
      calendar: null,
      smartMeter: null,
    };
  }

  // Docker Management API methods
  async getContainers(): Promise<ContainerInfo[]> {
    return this.fetchWithErrorHandling<ContainerInfo[]>(`${API_BASE_URL}/v1/docker/containers`);
  }

  async startContainer(serviceName: string): Promise<ContainerOperationResponse> {
    return this.fetchWithErrorHandling<ContainerOperationResponse>(
      `${API_BASE_URL}/v1/docker/containers/${serviceName}/start`,
      { method: 'POST' }
    );
  }

  async stopContainer(serviceName: string): Promise<ContainerOperationResponse> {
    return this.fetchWithErrorHandling<ContainerOperationResponse>(
      `${API_BASE_URL}/v1/docker/containers/${serviceName}/stop`,
      { method: 'POST' }
    );
  }

  async restartContainer(serviceName: string): Promise<ContainerOperationResponse> {
    return this.fetchWithErrorHandling<ContainerOperationResponse>(
      `${API_BASE_URL}/v1/docker/containers/${serviceName}/restart`,
      { method: 'POST' }
    );
  }

  async getContainerLogs(serviceName: string, tail: number = 100): Promise<{ logs: string }> {
    return this.fetchWithErrorHandling<{ logs: string }>(
      `${API_BASE_URL}/v1/docker/containers/${serviceName}/logs?tail=${tail}`
    );
  }

  async getContainerStats(serviceName: string): Promise<ContainerStats> {
    return this.fetchWithErrorHandling<ContainerStats>(
      `${API_BASE_URL}/v1/docker/containers/${serviceName}/stats`
    );
  }

  // API Key Management methods
  async getAPIKeys(): Promise<APIKeyInfo[]> {
    return this.fetchWithErrorHandling<APIKeyInfo[]>(`${API_BASE_URL}/v1/docker/api-keys`);
  }

  async updateAPIKey(service: string, apiKey: string): Promise<ContainerOperationResponse> {
    return this.fetchWithErrorHandling<ContainerOperationResponse>(
      `${API_BASE_URL}/v1/docker/api-keys/${service}`,
      {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ api_key: apiKey })
      }
    );
  }

  async testAPIKey(service: string, apiKey: string): Promise<APIKeyTestResponse> {
    return this.fetchWithErrorHandling<APIKeyTestResponse>(
      `${API_BASE_URL}/v1/docker/api-keys/${service}/test`,
      {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ api_key: apiKey })
      }
    );
  }
}

export const apiService = new ApiService();

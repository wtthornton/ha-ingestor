import { SystemHealth, Statistics, EventData, Configuration, ApiResponse, ErrorResponse } from '../types';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || '/api/v1';

class ApiService {
  private baseUrl: string;
  private authToken: string | null = null;

  constructor(baseUrl: string = API_BASE_URL) {
    this.baseUrl = baseUrl;
    this.authToken = localStorage.getItem('auth_token');
  }

  private async request<T>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<ApiResponse<T>> {
    const url = `${this.baseUrl}${endpoint}`;
    const headers: HeadersInit = {
      'Content-Type': 'application/json',
      ...options.headers,
    };

    if (this.authToken) {
      headers.Authorization = `Bearer ${this.authToken}`;
    }

    try {
      const response = await fetch(url, {
        ...options,
        headers,
      });

      if (!response.ok) {
        const errorData: ErrorResponse = await response.json();
        throw new Error(errorData.error || `HTTP ${response.status}`);
      }

      const data: ApiResponse<T> = await response.json();
      return data;
    } catch (error) {
      console.error(`API request failed for ${endpoint}:`, error);
      throw error;
    }
  }

  // Health endpoints
  async getHealth(): Promise<SystemHealth> {
    const response = await this.request<SystemHealth>('/health');
    return response.data!;
  }

  // Statistics endpoints
  async getStatistics(period: string = '1h'): Promise<Statistics> {
    const response = await this.request<Statistics>(`/stats?period=${period}`);
    return response.data!;
  }

  async getServicesStats(): Promise<Record<string, any>> {
    const response = await this.request<Record<string, any>>('/stats/services');
    return response.data!;
  }

  async getPerformanceStats(): Promise<Record<string, any>> {
    const response = await this.request<Record<string, any>>('/stats/performance');
    return response.data!;
  }

  async getAlerts(): Promise<any[]> {
    const response = await this.request<any[]>('/stats/alerts');
    return response.data!;
  }

  // Events endpoints
  async getEvents(params: {
    limit?: number;
    offset?: number;
    entity_id?: string;
    event_type?: string;
    start_time?: string;
    end_time?: string;
  } = {}): Promise<EventData[]> {
    const searchParams = new URLSearchParams();
    Object.entries(params).forEach(([key, value]) => {
      if (value !== undefined) {
        searchParams.append(key, value.toString());
      }
    });

    const queryString = searchParams.toString();
    const endpoint = queryString ? `/events?${queryString}` : '/events';
    
    const response = await this.request<EventData[]>(endpoint);
    return response.data!;
  }

  async getEventById(id: string): Promise<EventData> {
    const response = await this.request<EventData>(`/events/${id}`);
    return response.data!;
  }

  async searchEvents(query: string, fields: string[] = ['entity_id', 'event_type', 'attributes']): Promise<EventData[]> {
    const response = await this.request<EventData[]>('/events/search', {
      method: 'POST',
      body: JSON.stringify({ query, fields, limit: 100 }),
    });
    return response.data!;
  }

  async getEventsStats(period: string = '1h'): Promise<Record<string, any>> {
    const response = await this.request<Record<string, any>>(`/events/stats?period=${period}`);
    return response.data!;
  }

  async getActiveEntities(limit: number = 100): Promise<any[]> {
    const response = await this.request<any[]>(`/events/entities?limit=${limit}`);
    return response.data!;
  }

  async getEventTypes(limit: number = 50): Promise<any[]> {
    const response = await this.request<any[]>(`/events/types?limit=${limit}`);
    return response.data!;
  }

  // Configuration endpoints
  async getConfiguration(includeSensitive: boolean = false): Promise<Configuration> {
    const response = await this.request<Configuration>(`/config?include_sensitive=${includeSensitive}`);
    return response.data!;
  }

  async getConfigSchema(): Promise<Record<string, any>> {
    const response = await this.request<Record<string, any>>('/config/schema');
    return response.data!;
  }

  async updateConfiguration(service: string, updates: any[]): Promise<Record<string, any>> {
    const response = await this.request<Record<string, any>>(`/config/${service}`, {
      method: 'PUT',
      body: JSON.stringify(updates),
    });
    return response.data!;
  }

  async validateConfiguration(service: string, config: Configuration): Promise<Record<string, any>> {
    const response = await this.request<Record<string, any>>(`/config/${service}/validate`, {
      method: 'POST',
      body: JSON.stringify(config),
    });
    return response.data!;
  }

  async backupConfiguration(service: string): Promise<Record<string, any>> {
    const response = await this.request<Record<string, any>>(`/config/${service}/backup`);
    return response.data!;
  }

  async restoreConfiguration(service: string, backupData: any): Promise<Record<string, any>> {
    const response = await this.request<Record<string, any>>(`/config/${service}/restore`, {
      method: 'POST',
      body: JSON.stringify(backupData),
    });
    return response.data!;
  }

  async getConfigHistory(service: string, limit: number = 10): Promise<any[]> {
    const response = await this.request<any[]>(`/config/${service}/history?limit=${limit}`);
    return response.data!;
  }

  // Authentication
  async login(username: string, password: string): Promise<{ access_token: string; token_type: string }> {
    const response = await this.request<{ access_token: string; token_type: string }>('/token', {
      method: 'POST',
      body: JSON.stringify({ username, password }),
    });
    
    const tokenData = response.data!;
    this.authToken = tokenData.access_token;
    localStorage.setItem('auth_token', tokenData.access_token);
    
    return tokenData;
  }

  logout(): void {
    this.authToken = null;
    localStorage.removeItem('auth_token');
  }

  isAuthenticated(): boolean {
    return this.authToken !== null;
  }
}

// Create singleton instance
export const apiService = new ApiService();
export default apiService;

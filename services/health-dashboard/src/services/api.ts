import { HealthStatus, Statistics, DataSourceHealth, DataSourceMetrics } from '../types';

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
    return this.fetchWithErrorHandling<HealthStatus>(`${API_BASE_URL}/health`);
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
    const [carbon, pricing, air, calendar, meter] = await Promise.allSettled([
      this.getDataSourceHealth(8010),
      this.getDataSourceHealth(8011),
      this.getDataSourceHealth(8012),
      this.getDataSourceHealth(8013),
      this.getDataSourceHealth(8014),
    ]);

    return {
      carbonIntensity: carbon.status === 'fulfilled' ? carbon.value : null,
      electricityPricing: pricing.status === 'fulfilled' ? pricing.value : null,
      airQuality: air.status === 'fulfilled' ? air.value : null,
      calendar: calendar.status === 'fulfilled' ? calendar.value : null,
      smartMeter: meter.status === 'fulfilled' ? meter.value : null,
    };
  }
}

export const apiService = new ApiService();

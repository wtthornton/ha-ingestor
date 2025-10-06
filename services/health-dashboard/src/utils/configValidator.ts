/**
 * Configuration Validation Utility
 * 
 * This utility helps validate API response structures and provides
 * safe defaults to prevent frontend crashes when API responses
 * don't match expected formats.
 */

export interface ValidationResult {
  isValid: boolean;
  errors: string[];
  warnings: string[];
  safeData: any;
}

export class ConfigValidator {
  /**
   * Validate and sanitize health data structure
   */
  static validateHealthData(data: any): ValidationResult {
    const errors: string[] = [];
    const warnings: string[] = [];
    
    if (!data) {
      errors.push('Health data is null or undefined');
      return {
        isValid: false,
        errors,
        warnings,
        safeData: this.getDefaultHealthData()
      };
    }

    // Validate required fields
    if (!data.overall_status) {
      errors.push('Missing overall_status field');
    }

    if (!data.ingestion_service) {
      errors.push('Missing ingestion_service field');
    } else {
      // Validate ingestion service structure
      const ingestionService = data.ingestion_service;
      
      if (!ingestionService.websocket_connection) {
        warnings.push('Missing websocket_connection field, using defaults');
      }
      
      if (!ingestionService.event_processing) {
        warnings.push('Missing event_processing field, using defaults');
      }
      
      if (!ingestionService.weather_enrichment) {
        warnings.push('Missing weather_enrichment field, using defaults');
      }
      
      if (!ingestionService.influxdb_storage) {
        warnings.push('Missing influxdb_storage field, using defaults');
      }
    }

    // Create safe data with defaults for missing fields
    const safeData = {
      overall_status: data.overall_status || 'unknown',
      admin_api_status: data.admin_api_status || 'unknown',
      ingestion_service: {
        status: data.ingestion_service?.status || 'unknown',
        websocket_connection: {
          is_connected: data.ingestion_service?.websocket_connection?.is_connected ?? false,
          last_connection_time: data.ingestion_service?.websocket_connection?.last_connection_time || new Date().toISOString(),
          connection_attempts: data.ingestion_service?.websocket_connection?.connection_attempts || 0,
          last_error: data.ingestion_service?.websocket_connection?.last_error || null
        },
        event_processing: {
          events_per_minute: data.ingestion_service?.event_processing?.events_per_minute || 0,
          total_events: data.ingestion_service?.event_processing?.total_events || 0,
          error_rate: data.ingestion_service?.event_processing?.error_rate || 0
        },
        weather_enrichment: {
          enabled: data.ingestion_service?.weather_enrichment?.enabled ?? false,
          cache_hits: data.ingestion_service?.weather_enrichment?.cache_hits || 0,
          api_calls: data.ingestion_service?.weather_enrichment?.api_calls || 0,
          last_error: data.ingestion_service?.weather_enrichment?.last_error || null
        },
        influxdb_storage: {
          is_connected: data.ingestion_service?.influxdb_storage?.is_connected ?? false,
          last_write_time: data.ingestion_service?.influxdb_storage?.last_write_time || new Date().toISOString(),
          write_errors: data.ingestion_service?.influxdb_storage?.write_errors || 0
        },
        timestamp: data.ingestion_service?.timestamp || new Date().toISOString()
      },
      timestamp: data.timestamp || new Date().toISOString()
    };

    return {
      isValid: errors.length === 0,
      errors,
      warnings,
      safeData
    };
  }

  /**
   * Validate and sanitize statistics data structure
   */
  static validateStatisticsData(data: any): ValidationResult {
    const errors: string[] = [];
    const warnings: string[] = [];
    
    if (!data) {
      errors.push('Statistics data is null or undefined');
      return {
        isValid: false,
        errors,
        warnings,
        safeData: this.getDefaultStatisticsData()
      };
    }

    const safeData = {
      timestamp: data.timestamp || new Date().toISOString(),
      period: data.period || '1h',
      metrics: data.metrics || {},
      trends: data.trends || {},
      alerts: data.alerts || []
    };

    return {
      isValid: errors.length === 0,
      errors,
      warnings,
      safeData
    };
  }

  /**
   * Validate and sanitize events data structure
   */
  static validateEventsData(data: any[]): ValidationResult {
    const errors: string[] = [];
    const warnings: string[] = [];
    
    if (!Array.isArray(data)) {
      errors.push('Events data is not an array');
      return {
        isValid: false,
        errors,
        warnings,
        safeData: []
      };
    }

    const safeData = data.map(event => ({
      id: event.id || `event_${Date.now()}_${Math.random()}`,
      timestamp: event.timestamp || new Date().toISOString(),
      entity_id: event.entity_id || 'unknown',
      event_type: event.event_type || 'unknown',
      old_state: event.old_state || null,
      new_state: event.new_state || null,
      attributes: event.attributes || {},
      tags: event.tags || {}
    }));

    return {
      isValid: errors.length === 0,
      errors,
      warnings,
      safeData
    };
  }

  /**
   * Get default health data structure
   */
  private static getDefaultHealthData() {
    return {
      overall_status: 'unknown',
      admin_api_status: 'unknown',
      ingestion_service: {
        status: 'unknown',
        websocket_connection: {
          is_connected: false,
          last_connection_time: new Date().toISOString(),
          connection_attempts: 0,
          last_error: null
        },
        event_processing: {
          events_per_minute: 0,
          total_events: 0,
          error_rate: 0
        },
        weather_enrichment: {
          enabled: false,
          cache_hits: 0,
          api_calls: 0,
          last_error: null
        },
        influxdb_storage: {
          is_connected: false,
          last_write_time: new Date().toISOString(),
          write_errors: 0
        },
        timestamp: new Date().toISOString()
      },
      timestamp: new Date().toISOString()
    };
  }

  /**
   * Get default statistics data structure
   */
  private static getDefaultStatisticsData() {
    return {
      timestamp: new Date().toISOString(),
      period: '1h',
      metrics: {},
      trends: {},
      alerts: []
    };
  }

  /**
   * Log validation results for debugging
   */
  static logValidationResult(result: ValidationResult, context: string) {
    if (result.errors.length > 0) {
      console.error(`[ConfigValidator] ${context} - Errors:`, result.errors);
    }
    
    if (result.warnings.length > 0) {
      console.warn(`[ConfigValidator] ${context} - Warnings:`, result.warnings);
    }
    
    if (result.isValid && result.warnings.length === 0) {
      console.log(`[ConfigValidator] ${context} - Validation passed`);
    }
  }
}

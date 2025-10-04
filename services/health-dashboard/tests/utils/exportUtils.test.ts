import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import {
  exportEventsToCSV,
  exportEventsToJSON,
  exportEventsToExcel,
  performHistoricalAnalysis,
  ExportHistoryManager,
  ExportOptions,
  HistoricalAnalysisOptions,
} from '../../src/utils/exportUtils';
import { EventData } from '../../src/types';

// Mock DOM methods
const mockCreateElement = vi.fn();
const mockAppendChild = vi.fn();
const mockRemoveChild = vi.fn();
const mockClick = vi.fn();
const mockCreateObjectURL = vi.fn();
const mockRevokeObjectURL = vi.fn();

// Mock localStorage
const mockLocalStorage = {
  getItem: vi.fn(),
  setItem: vi.fn(),
  removeItem: vi.fn(),
};

describe('Export Utils', () => {
  beforeEach(() => {
    // Reset mocks
    vi.clearAllMocks();
    
    // Mock DOM
    global.document.createElement = mockCreateElement;
    global.document.body.appendChild = mockAppendChild;
    global.document.body.removeChild = mockRemoveChild;
    global.URL.createObjectURL = mockCreateObjectURL;
    global.URL.revokeObjectURL = mockRevokeObjectURL;
    
    // Mock localStorage
    Object.defineProperty(window, 'localStorage', {
      value: mockLocalStorage,
      writable: true,
    });
    
    // Mock link element
    const mockLink = {
      setAttribute: vi.fn(),
      click: mockClick,
      style: {},
    };
    mockCreateElement.mockReturnValue(mockLink);
    
    // Mock blob
    const mockBlob = {};
    mockCreateObjectURL.mockReturnValue('mock-url');
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  describe('exportEventsToCSV', () => {
    const mockEvents: EventData[] = [
      {
        id: '1',
        timestamp: '2024-01-01T00:00:00Z',
        entity_id: 'sensor.temperature',
        event_type: 'state_changed',
        new_state: { state: '20.5' },
        attributes: { unit_of_measurement: '°C' },
        domain: 'sensor',
        service: null,
        context: { id: 'context-1' },
      },
      {
        id: '2',
        timestamp: '2024-01-01T01:00:00Z',
        entity_id: 'sensor.humidity',
        event_type: 'state_changed',
        new_state: { state: '65' },
        attributes: { unit_of_measurement: '%' },
        domain: 'sensor',
        service: null,
        context: { id: 'context-2' },
      },
    ];

    it('should export events to CSV successfully', () => {
      const options: ExportOptions = {
        filename: 'test-export.csv',
        includeMetadata: true,
      };

      const result = exportEventsToCSV(mockEvents, options);

      expect(result.success).toBe(true);
      expect(result.filename).toBe('test-export.csv');
      expect(result.progress).toBe(100);
      expect(mockCreateElement).toHaveBeenCalledWith('a');
      expect(mockClick).toHaveBeenCalled();
    });

    it('should handle empty events array', () => {
      const result = exportEventsToCSV([], {});

      expect(result.success).toBe(true);
      expect(mockCreateElement).toHaveBeenCalled();
    });

    it('should include metadata when requested', () => {
      const options: ExportOptions = {
        includeMetadata: true,
        dateRange: {
          start: new Date('2024-01-01'),
          end: new Date('2024-01-02'),
        },
      };

      const result = exportEventsToCSV(mockEvents, options);

      expect(result.success).toBe(true);
    });

    it('should handle export errors gracefully', () => {
      mockCreateElement.mockImplementation(() => {
        throw new Error('DOM error');
      });

      const result = exportEventsToCSV(mockEvents, {});

      expect(result.success).toBe(false);
      expect(result.error).toBe('DOM error');
    });
  });

  describe('exportEventsToJSON', () => {
    const mockEvents: EventData[] = [
      {
        id: '1',
        timestamp: '2024-01-01T00:00:00Z',
        entity_id: 'sensor.temperature',
        event_type: 'state_changed',
        new_state: { state: '20.5' },
        attributes: { unit_of_measurement: '°C' },
        domain: 'sensor',
        service: null,
        context: { id: 'context-1' },
      },
    ];

    it('should export events to JSON successfully', () => {
      const options: ExportOptions = {
        filename: 'test-export.json',
        includeMetadata: true,
      };

      const result = exportEventsToJSON(mockEvents, options);

      expect(result.success).toBe(true);
      expect(result.filename).toBe('test-export.json');
      expect(result.progress).toBe(100);
    });

    it('should include metadata in JSON export', () => {
      const options: ExportOptions = {
        includeMetadata: true,
        title: 'Test Export',
        filters: { entity_id: 'sensor.temperature' },
      };

      const result = exportEventsToJSON(mockEvents, options);

      expect(result.success).toBe(true);
    });

    it('should handle export errors gracefully', () => {
      mockCreateElement.mockImplementation(() => {
        throw new Error('JSON export error');
      });

      const result = exportEventsToJSON(mockEvents, {});

      expect(result.success).toBe(false);
      expect(result.error).toBe('JSON export error');
    });
  });

  describe('exportEventsToExcel', () => {
    const mockEvents: EventData[] = [
      {
        id: '1',
        timestamp: '2024-01-01T00:00:00Z',
        entity_id: 'sensor.temperature',
        event_type: 'state_changed',
        new_state: { state: '20.5' },
        attributes: { unit_of_measurement: '°C' },
        domain: 'sensor',
        service: null,
        context: { id: 'context-1' },
      },
    ];

    it('should export events to Excel format (converted to CSV)', () => {
      const options: ExportOptions = {
        filename: 'test-export.xlsx',
      };

      const result = exportEventsToExcel(mockEvents, options);

      expect(result.success).toBe(true);
      expect(result.filename).toBe('test-export.csv');
      expect(result.error).toBe('Excel export converted to CSV format');
    });

    it('should handle Excel export errors gracefully', () => {
      mockCreateElement.mockImplementation(() => {
        throw new Error('Excel export error');
      });

      const result = exportEventsToExcel(mockEvents, {});

      expect(result.success).toBe(false);
      expect(result.error).toBe('Excel export error');
    });
  });

  describe('performHistoricalAnalysis', () => {
    const mockEvents: EventData[] = [
      {
        id: '1',
        timestamp: '2024-01-01T00:00:00Z',
        entity_id: 'sensor.temperature',
        event_type: 'state_changed',
        new_state: { state: '20.5' },
        attributes: { unit_of_measurement: '°C' },
        domain: 'sensor',
        service: null,
        context: { id: 'context-1' },
      },
      {
        id: '2',
        timestamp: '2024-01-01T01:00:00Z',
        entity_id: 'sensor.temperature',
        event_type: 'state_changed',
        new_state: { state: '21.0' },
        attributes: { unit_of_measurement: '°C' },
        domain: 'sensor',
        service: null,
        context: { id: 'context-2' },
      },
      {
        id: '3',
        timestamp: '2024-01-02T00:00:00Z',
        entity_id: 'sensor.temperature',
        event_type: 'state_changed',
        new_state: { state: '19.5' },
        attributes: { unit_of_measurement: '°C' },
        domain: 'sensor',
        service: null,
        context: { id: 'context-3' },
      },
    ];

    it('should perform historical analysis with day aggregation', () => {
      const options: HistoricalAnalysisOptions = {
        timeRange: {
          start: new Date('2024-01-01'),
          end: new Date('2024-01-02'),
        },
        aggregation: 'day',
        metrics: ['event_count'],
        groupBy: ['entity_id'],
      };

      const result = performHistoricalAnalysis(mockEvents, options);

      expect(result.labels).toBeDefined();
      expect(result.datasets).toBeDefined();
      expect(result.datasets.length).toBe(1);
      expect(result.datasets[0].label).toBe('event_count');
    });

    it('should filter events by time range', () => {
      const options: HistoricalAnalysisOptions = {
        timeRange: {
          start: new Date('2024-01-01T00:30:00Z'),
          end: new Date('2024-01-01T01:30:00Z'),
        },
        aggregation: 'hour',
        metrics: ['event_count'],
      };

      const result = performHistoricalAnalysis(mockEvents, options);

      expect(result.labels.length).toBeGreaterThan(0);
      expect(result.datasets[0].data.length).toBe(result.labels.length);
    });

    it('should handle different aggregation periods', () => {
      const options: HistoricalAnalysisOptions = {
        timeRange: {
          start: new Date('2024-01-01'),
          end: new Date('2024-01-02'),
        },
        aggregation: 'week',
        metrics: ['event_count'],
      };

      const result = performHistoricalAnalysis(mockEvents, options);

      expect(result.labels).toBeDefined();
      expect(result.datasets).toBeDefined();
    });
  });

  describe('ExportHistoryManager', () => {
    beforeEach(() => {
      mockLocalStorage.getItem.mockReturnValue(null);
    });

    it('should get empty history when none exists', () => {
      const history = ExportHistoryManager.getHistory();

      expect(history).toEqual([]);
      expect(mockLocalStorage.getItem).toHaveBeenCalledWith('export-history');
    });

    it('should get existing history from localStorage', () => {
      const mockHistory = [
        {
          id: 'export-1',
          filename: 'test.csv',
          format: 'csv',
          timestamp: '2024-01-01T00:00:00.000Z',
          size: 100,
          status: 'completed' as const,
          options: {},
        },
      ];

      mockLocalStorage.getItem.mockReturnValue(JSON.stringify(mockHistory));

      const history = ExportHistoryManager.getHistory();

      expect(history).toEqual(mockHistory);
    });

    it('should add item to history', () => {
      const item = {
        filename: 'test.csv',
        format: 'csv',
        size: 100,
        status: 'completed' as const,
        options: {},
      };

      const result = ExportHistoryManager.addToHistory(item);

      expect(result.id).toBeDefined();
      expect(result.timestamp).toBeInstanceOf(Date);
      expect(result.filename).toBe('test.csv');
      expect(mockLocalStorage.setItem).toHaveBeenCalled();
    });

    it('should remove item from history', () => {
      const mockHistory = [
        {
          id: 'export-1',
          filename: 'test.csv',
          format: 'csv',
          timestamp: new Date('2024-01-01'),
          size: 100,
          status: 'completed' as const,
          options: {},
        },
      ];

      mockLocalStorage.getItem.mockReturnValue(JSON.stringify(mockHistory));

      ExportHistoryManager.removeFromHistory('export-1');

      expect(mockLocalStorage.setItem).toHaveBeenCalledWith(
        'export-history',
        JSON.stringify([])
      );
    });

    it('should clear all history', () => {
      ExportHistoryManager.clearHistory();

      expect(mockLocalStorage.removeItem).toHaveBeenCalledWith('export-history');
    });

    it('should limit history to 50 items', () => {
      const largeHistory = Array.from({ length: 60 }, (_, i) => ({
        id: `export-${i}`,
        filename: `test-${i}.csv`,
        format: 'csv',
        timestamp: new Date(),
        size: 100,
        status: 'completed' as const,
        options: {},
      }));

      mockLocalStorage.getItem.mockReturnValue(JSON.stringify(largeHistory));

      const item = {
        filename: 'new-test.csv',
        format: 'csv',
        size: 100,
        status: 'completed' as const,
        options: {},
      };

      ExportHistoryManager.addToHistory(item);

      expect(mockLocalStorage.setItem).toHaveBeenCalled();
      const setItemCall = mockLocalStorage.setItem.mock.calls[0];
      const savedHistory = JSON.parse(setItemCall[1]);
      expect(savedHistory.length).toBe(50);
    });

    it('should handle localStorage errors gracefully', () => {
      mockLocalStorage.getItem.mockImplementation(() => {
        throw new Error('localStorage error');
      });

      const history = ExportHistoryManager.getHistory();

      expect(history).toEqual([]);
    });
  });
});
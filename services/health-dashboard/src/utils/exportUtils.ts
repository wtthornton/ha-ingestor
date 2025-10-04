import html2canvas from 'html2canvas';
import jsPDF from 'jspdf';
import { ChartData, EventData } from '../types';

export interface ExportOptions {
  filename?: string;
  title?: string;
  includeMetadata?: boolean;
  dateRange?: { start: Date; end: Date };
  filters?: Record<string, any>;
}

export interface ExportResult {
  success: boolean;
  downloadUrl?: string;
  error?: string;
  progress?: number;
  filename?: string;
}

export interface HistoricalAnalysisOptions {
  timeRange: { start: Date; end: Date };
  aggregation: 'hour' | 'day' | 'week' | 'month';
  metrics: string[];
  groupBy?: string[];
}

export interface ExportHistoryItem {
  id: string;
  filename: string;
  format: string;
  timestamp: Date;
  size: number;
  status: 'completed' | 'failed' | 'processing';
  options: ExportOptions;
}

export const exportToCSV = (data: ChartData, options: ExportOptions = {}): void => {
  const { filename = 'chart-data.csv', includeMetadata = true } = options;
  
  let csvContent = '';
  
  if (includeMetadata) {
    csvContent += `Chart Data Export\n`;
    csvContent += `Generated: ${new Date().toISOString()}\n`;
    csvContent += `Title: ${options.title || 'Untitled Chart'}\n\n`;
  }
  
  // Add headers
  csvContent += 'Label,' + data.datasets.map(dataset => dataset.label).join(',') + '\n';
  
  // Add data rows
  data.labels.forEach((label, index) => {
    const row = [label];
    data.datasets.forEach(dataset => {
      const value = dataset.data[index];
      row.push(typeof value === 'number' ? value.toString() : '');
    });
    csvContent += row.join(',') + '\n';
  });
  
  // Create and download file
  const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
  const link = document.createElement('a');
  const url = URL.createObjectURL(blob);
  link.setAttribute('href', url);
  link.setAttribute('download', filename);
  link.style.visibility = 'hidden';
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  URL.revokeObjectURL(url);
};

export const exportToJSON = (data: ChartData, options: ExportOptions = {}): void => {
  const { filename = 'chart-data.json', includeMetadata = true } = options;
  
  const exportData = {
    ...(includeMetadata && {
      metadata: {
        title: options.title || 'Untitled Chart',
        exportedAt: new Date().toISOString(),
        version: '1.0',
      },
    }),
    chartData: data,
  };
  
  const jsonContent = JSON.stringify(exportData, null, 2);
  
  // Create and download file
  const blob = new Blob([jsonContent], { type: 'application/json;charset=utf-8;' });
  const link = document.createElement('a');
  const url = URL.createObjectURL(blob);
  link.setAttribute('href', url);
  link.setAttribute('download', filename);
  link.style.visibility = 'hidden';
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  URL.revokeObjectURL(url);
};

export const exportToPDF = async (
  chartElement: HTMLElement,
  options: ExportOptions = {}
): Promise<void> => {
  if (!chartElement) {
    throw new Error('Chart element is required for PDF export');
  }
  
  const { filename = 'chart-export.pdf', title = 'Chart Export' } = options;
  
  try {
    // Capture the chart as canvas
    const canvas = await html2canvas(chartElement, {
      backgroundColor: '#ffffff',
      scale: 2, // Higher resolution
      useCORS: true,
      allowTaint: true,
    });
    
    // Create PDF
    const imgData = canvas.toDataURL('image/png');
    const pdf = new jsPDF({
      orientation: 'landscape',
      unit: 'mm',
      format: 'a4',
    });
    
    // Add title
    pdf.setFontSize(16);
    pdf.setFont('helvetica', 'bold');
    pdf.text(title, 20, 20);
    
    // Add timestamp
    pdf.setFontSize(10);
    pdf.setFont('helvetica', 'normal');
    pdf.text(`Generated: ${new Date().toLocaleString()}`, 20, 30);
    
    // Calculate image dimensions to fit page
    const pageWidth = pdf.internal.pageSize.getWidth();
    const pageHeight = pdf.internal.pageSize.getHeight();
    const imgWidth = pageWidth - 40; // 20mm margin on each side
    const imgHeight = (canvas.height * imgWidth) / canvas.width;
    
    // Add image
    pdf.addImage(imgData, 'PNG', 20, 40, imgWidth, imgHeight);
    
    // Save PDF
    pdf.save(filename);
  } catch (error) {
    console.error('Error exporting to PDF:', error);
    throw new Error('Failed to export chart to PDF');
  }
};

export const exportChartData = async (
  data: ChartData,
  format: 'csv' | 'json' | 'pdf',
  chartElement?: HTMLElement,
  options: ExportOptions = {}
): Promise<void> => {
  switch (format) {
    case 'csv':
      exportToCSV(data, options);
      break;
    case 'json':
      exportToJSON(data, options);
      break;
    case 'pdf':
      if (!chartElement) {
        throw new Error('Chart element is required for PDF export');
      }
      await exportToPDF(chartElement, options);
      break;
    default:
      throw new Error(`Unsupported export format: ${format}`);
  }
};

export const getExportFilename = (title: string, format: string): string => {
  const sanitizedTitle = title
    .toLowerCase()
    .replace(/[^a-z0-9\s-]/g, '')
    .replace(/\s+/g, '-')
    .trim();
  
  const timestamp = new Date().toISOString().split('T')[0];
  return `${sanitizedTitle}-${timestamp}.${format}`;
};

// Enhanced export functions for events and historical data
export const exportEventsToCSV = (
  events: EventData[], 
  options: ExportOptions = {}
): ExportResult => {
  try {
    const { filename = 'events-export.csv', includeMetadata = true } = options;
    
    let csvContent = '';
    
    if (includeMetadata) {
      csvContent += `Events Export\n`;
      csvContent += `Generated: ${new Date().toISOString()}\n`;
      csvContent += `Total Events: ${events.length}\n`;
      if (options.dateRange) {
        csvContent += `Date Range: ${options.dateRange.start.toISOString()} to ${options.dateRange.end.toISOString()}\n`;
      }
      csvContent += `\n`;
    }
    
    // Headers
    const headers = [
      'ID', 'Timestamp', 'Entity ID', 'Event Type', 'State', 
      'Attributes', 'Domain', 'Service', 'Context'
    ];
    csvContent += headers.join(',') + '\n';
    
    // Data rows
    events.forEach(event => {
      const row = [
        event.id,
        event.timestamp,
        event.entity_id,
        event.event_type,
        event.new_state?.state || '',
        JSON.stringify(event.attributes || {}),
        event.domain || '',
        event.service || '',
        JSON.stringify(event.context || {})
      ];
      csvContent += row.map(cell => `"${cell}"`).join(',') + '\n';
    });
    
    // Create and download file
    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.setAttribute('href', url);
    link.setAttribute('download', filename);
    link.style.visibility = 'hidden';
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
    
    return {
      success: true,
      downloadUrl: url,
      filename,
      progress: 100
    };
  } catch (error) {
    return {
      success: false,
      error: error instanceof Error ? error.message : 'Export failed'
    };
  }
};

export const exportEventsToJSON = (
  events: EventData[], 
  options: ExportOptions = {}
): ExportResult => {
  try {
    const { filename = 'events-export.json', includeMetadata = true } = options;
    
    const exportData = {
      ...(includeMetadata && {
        metadata: {
          title: options.title || 'Events Export',
          exportedAt: new Date().toISOString(),
          totalEvents: events.length,
          dateRange: options.dateRange,
          filters: options.filters,
          version: '1.0',
        },
      }),
      events,
    };
    
    const jsonContent = JSON.stringify(exportData, null, 2);
    
    // Create and download file
    const blob = new Blob([jsonContent], { type: 'application/json;charset=utf-8;' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.setAttribute('href', url);
    link.setAttribute('download', filename);
    link.style.visibility = 'hidden';
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
    
    return {
      success: true,
      downloadUrl: url,
      filename,
      progress: 100
    };
  } catch (error) {
    return {
      success: false,
      error: error instanceof Error ? error.message : 'Export failed'
    };
  }
};

export const exportEventsToExcel = (
  events: EventData[], 
  options: ExportOptions = {}
): ExportResult => {
  try {
    const { filename = 'events-export.xlsx', includeMetadata = true } = options;
    
    // For now, we'll create a CSV with .xlsx extension
    // In a real implementation, you'd use a library like xlsx
    const csvResult = exportEventsToCSV(events, { ...options, filename });
    
    if (csvResult.success) {
      return {
        ...csvResult,
        filename: filename.replace('.xlsx', '.csv'),
        error: 'Excel export converted to CSV format'
      };
    }
    
    return csvResult;
  } catch (error) {
    return {
      success: false,
      error: error instanceof Error ? error.message : 'Excel export failed'
    };
  }
};

// Historical analysis functions
export const performHistoricalAnalysis = (
  events: EventData[],
  options: HistoricalAnalysisOptions
): ChartData => {
  const { timeRange, aggregation, metrics, groupBy } = options;
  
  // Filter events by time range
  const filteredEvents = events.filter(event => {
    const eventTime = new Date(event.timestamp);
    return eventTime >= timeRange.start && eventTime <= timeRange.end;
  });
  
  // Group events by time intervals
  const timeGroups = new Map<string, EventData[]>();
  
  filteredEvents.forEach(event => {
    const eventTime = new Date(event.timestamp);
    let timeKey: string;
    
    switch (aggregation) {
      case 'hour':
        timeKey = eventTime.toISOString().slice(0, 13) + ':00:00Z';
        break;
      case 'day':
        timeKey = eventTime.toISOString().slice(0, 10);
        break;
      case 'week':
        const weekStart = new Date(eventTime);
        weekStart.setDate(eventTime.getDate() - eventTime.getDay());
        timeKey = weekStart.toISOString().slice(0, 10);
        break;
      case 'month':
        timeKey = eventTime.toISOString().slice(0, 7);
        break;
      default:
        timeKey = eventTime.toISOString().slice(0, 10);
    }
    
    if (!timeGroups.has(timeKey)) {
      timeGroups.set(timeKey, []);
    }
    timeGroups.get(timeKey)!.push(event);
  });
  
  // Create chart data
  const labels = Array.from(timeGroups.keys()).sort();
  const datasets = metrics.map(metric => ({
    label: metric,
    data: labels.map(label => {
      const events = timeGroups.get(label) || [];
      return events.length; // Simple count for now
    }),
    borderColor: `hsl(${Math.random() * 360}, 70%, 50%)`,
    backgroundColor: `hsla(${Math.random() * 360}, 70%, 50%, 0.1)`,
  }));
  
  return {
    labels,
    datasets,
  };
};

// Export history management
export class ExportHistoryManager {
  private static STORAGE_KEY = 'export-history';
  
  static getHistory(): ExportHistoryItem[] {
    try {
      const stored = localStorage.getItem(this.STORAGE_KEY);
      return stored ? JSON.parse(stored) : [];
    } catch {
      return [];
    }
  }
  
  static addToHistory(item: Omit<ExportHistoryItem, 'id' | 'timestamp'>): ExportHistoryItem {
    const historyItem: ExportHistoryItem = {
      ...item,
      id: `export-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
      timestamp: new Date(),
    };
    
    const history = this.getHistory();
    history.unshift(historyItem);
    
    // Keep only last 50 exports
    if (history.length > 50) {
      history.splice(50);
    }
    
    localStorage.setItem(this.STORAGE_KEY, JSON.stringify(history));
    return historyItem;
  }
  
  static removeFromHistory(id: string): void {
    const history = this.getHistory();
    const filtered = history.filter(item => item.id !== id);
    localStorage.setItem(this.STORAGE_KEY, JSON.stringify(filtered));
  }
  
  static clearHistory(): void {
    localStorage.removeItem(this.STORAGE_KEY);
  }
}

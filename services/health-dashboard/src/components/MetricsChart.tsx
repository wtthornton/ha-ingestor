import React, { useRef, useCallback } from 'react';
import { ChartData, ChartType } from '../types';
import { InteractiveChart, ChartFilters } from './InteractiveChart';
import { exportChartData, getExportFilename } from '../utils/exportUtils';

interface MetricsChartProps {
  data: ChartData;
  type: ChartType;
  title: string;
  loading?: boolean;
  height?: number;
  interactive?: boolean;
  realTime?: boolean;
  onFilter?: (filters: ChartFilters) => void;
}

export const MetricsChart: React.FC<MetricsChartProps> = ({
  data,
  type,
  title,
  loading = false,
  height = 300,
  interactive = true,
  realTime = false,
  onFilter,
}) => {
  const chartRef = useRef<HTMLDivElement>(null);

  const handleExport = useCallback(async (format: 'csv' | 'json' | 'pdf') => {
    try {
      const filename = getExportFilename(title, format);
      const options = {
        filename,
        title,
        includeMetadata: true,
      };

      if (format === 'pdf' && chartRef.current) {
        await exportChartData(data, format, chartRef.current, options);
      } else {
        exportChartData(data, format, undefined, options);
      }
    } catch (error) {
      console.error('Export failed:', error);
      // You could show a toast notification here
    }
  }, [data, title]);

  const handleFilter = useCallback((filters: ChartFilters) => {
    onFilter?.(filters);
  }, [onFilter]);

  if (interactive) {
    return (
      <div ref={chartRef}>
        <InteractiveChart
          data={data}
          type={type}
          title={title}
          loading={loading}
          height={height}
          onExport={handleExport}
          onFilter={handleFilter}
          realTime={realTime}
          enableZoom={true}
          enablePan={true}
          enableDrillDown={true}
        />
      </div>
    );
  }

  // Fallback to simple chart for non-interactive mode
  return (
    <div className="bg-white rounded-lg shadow-md p-6">
      <h3 className="text-lg font-semibold text-gray-900 mb-4">{title}</h3>
      <div style={{ height: `${height}px` }}>
        <div className="flex items-center justify-center h-full text-gray-500">
          Simple chart mode - use interactive=true for full features
        </div>
      </div>
    </div>
  );
};

import React, { useRef, useCallback, useState, useEffect } from 'react';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  ArcElement,
  Title,
  Tooltip,
  Legend,
  TimeScale,
} from 'chart.js';
import { Line, Bar, Doughnut } from 'react-chartjs-2';
import zoomPlugin from 'chartjs-plugin-zoom';
import 'chartjs-adapter-date-fns';
import { ChartData, ChartType } from '../types';
import { ChartSkeleton } from './SkeletonLoader';
import { ChartToolbar } from './ChartToolbar';
import { ChartFilter } from './ChartFilter';

// Register Chart.js components
ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  ArcElement,
  Title,
  Tooltip,
  Legend,
  TimeScale,
  zoomPlugin
);

interface InteractiveChartProps {
  data: ChartData;
  type: ChartType;
  title: string;
  loading?: boolean;
  height?: number;
  onExport?: (format: 'csv' | 'json' | 'pdf') => void;
  onFilter?: (filters: ChartFilters) => void;
  realTime?: boolean;
  enableZoom?: boolean;
  enablePan?: boolean;
  enableDrillDown?: boolean;
}

export interface ChartFilters {
  timeRange?: {
    start: Date;
    end: Date;
  };
  entityTypes?: string[];
  eventTypes?: string[];
  dataPoints?: number;
}

const getChartOptions = (
  type: ChartType,
  title: string,
  enableZoom: boolean = true,
  enablePan: boolean = true,
  onDrillDown?: (event: any) => void
) => {
  const baseOptions = {
    responsive: true,
    maintainAspectRatio: false,
    interaction: {
      mode: 'nearest' as const,
      intersect: false,
      axis: 'xy' as const,
    },
    plugins: {
      legend: {
        position: 'top' as const,
        labels: {
          usePointStyle: true,
          padding: 20,
        },
      },
      title: {
        display: true,
        text: title,
        font: {
          size: 16,
          weight: 'bold' as const,
        },
      },
      tooltip: {
        mode: 'index' as const,
        intersect: false,
        backgroundColor: 'rgba(0, 0, 0, 0.8)',
        titleColor: 'white',
        bodyColor: 'white',
        borderColor: 'rgba(255, 255, 255, 0.1)',
        borderWidth: 1,
        cornerRadius: 8,
        displayColors: true,
        callbacks: {
          title: (context: any) => {
            return context[0]?.label || '';
          },
          label: (context: any) => {
            const label = context.dataset.label || '';
            const value = context.parsed.y || context.parsed;
            return `${label}: ${value}`;
          },
        },
      },
      zoom: enableZoom ? {
        zoom: {
          wheel: {
            enabled: true,
          },
          pinch: {
            enabled: true,
          },
          mode: 'xy' as const,
        },
        pan: {
          enabled: enablePan,
          mode: 'xy' as const,
        },
        limits: {
          x: { min: 'original', max: 'original' },
          y: { min: 'original', max: 'original' },
        },
      } : undefined,
    },
    onClick: onDrillDown,
    onHover: (event: any, activeElements: any) => {
      if (event.native) {
        event.native.target.style.cursor = activeElements.length > 0 ? 'pointer' : 'default';
      }
    },
  };

  if (type === 'line' || type === 'bar') {
    return {
      ...baseOptions,
      scales: {
        x: {
          type: 'time' as const,
          time: {
            displayFormats: {
              hour: 'HH:mm',
              day: 'MMM dd',
              week: 'MMM dd',
              month: 'MMM yyyy',
            },
          },
          grid: {
            color: 'rgba(0, 0, 0, 0.1)',
            drawBorder: false,
          },
          ticks: {
            color: 'rgba(0, 0, 0, 0.7)',
            font: {
              size: 12,
            },
          },
        },
        y: {
          beginAtZero: true,
          grid: {
            color: 'rgba(0, 0, 0, 0.1)',
            drawBorder: false,
          },
          ticks: {
            color: 'rgba(0, 0, 0, 0.7)',
            font: {
              size: 12,
            },
          },
        },
      },
    };
  }

  return baseOptions;
};

export const InteractiveChart: React.FC<InteractiveChartProps> = ({
  data,
  type,
  title,
  loading = false,
  height = 300,
  onExport,
  onFilter,
  realTime = false,
  enableZoom = true,
  enablePan = true,
  enableDrillDown = true,
}) => {
  const chartRef = useRef<ChartJS>(null);
  const [filters, setFilters] = useState<ChartFilters>({});
  const [isZoomed, setIsZoomed] = useState(false);

  // Handle drill-down functionality
  const handleDrillDown = useCallback((event: any) => {
    if (!enableDrillDown || !event.native) return;
    
    const chart = chartRef.current;
    if (!chart) return;

    const points = chart.getElementsAtEventForMode(
      event,
      'nearest',
      { intersect: true },
      true
    );

    if (points.length > 0) {
      const point = points[0];
      const datasetIndex = point.datasetIndex;
      const dataIndex = point.index;
      
      // Emit drill-down event with data point information
      const drillDownData = {
        datasetIndex,
        dataIndex,
        label: data.labels[dataIndex],
        value: data.datasets[datasetIndex].data[dataIndex],
        dataset: data.datasets[datasetIndex],
      };
      
      console.log('Drill-down event:', drillDownData);
      // You can emit this to parent component or handle it here
    }
  }, [data, enableDrillDown]);

  // Handle zoom reset
  const handleZoomReset = useCallback(() => {
    const chart = chartRef.current;
    if (chart && chart.zoom) {
      chart.zoom.reset();
      setIsZoomed(false);
    }
  }, []);

  // Handle filter changes
  const handleFilterChange = useCallback((newFilters: ChartFilters) => {
    setFilters(newFilters);
    onFilter?.(newFilters);
  }, [onFilter]);

  // Handle export
  const handleExport = useCallback((format: 'csv' | 'json' | 'pdf') => {
    onExport?.(format);
  }, [onExport]);

  // Update zoom state when zoom changes
  useEffect(() => {
    const chart = chartRef.current;
    if (!chart) return;

    const handleZoom = () => {
      const zoom = chart.zoom;
      if (zoom) {
        const isZoomedState = zoom.getZoomLevel() > 1;
        setIsZoomed(isZoomedState);
      }
    };

    chart.canvas.addEventListener('wheel', handleZoom);
    chart.canvas.addEventListener('touchmove', handleZoom);

    return () => {
      chart.canvas.removeEventListener('wheel', handleZoom);
      chart.canvas.removeEventListener('touchmove', handleZoom);
    };
  }, []);

  if (loading) {
    return <ChartSkeleton height={height} />;
  }

  const options = getChartOptions(type, title, enableZoom, enablePan, handleDrillDown);

  const renderChart = () => {
    const commonProps = {
      ref: chartRef,
      data,
      options,
    };

    switch (type) {
      case 'line':
        return <Line {...commonProps} />;
      case 'bar':
        return <Bar {...commonProps} />;
      case 'doughnut':
      case 'pie':
        return <Doughnut {...commonProps} />;
      default:
        return <Line {...commonProps} />;
    }
  };

  return (
    <div className="bg-white rounded-lg shadow-md p-6">
      {/* Chart Toolbar */}
      <ChartToolbar
        title={title}
        isZoomed={isZoomed}
        onZoomReset={handleZoomReset}
        onExport={handleExport}
        realTime={realTime}
        enableZoom={enableZoom}
        enablePan={enablePan}
        enableDrillDown={enableDrillDown}
      />

      {/* Chart Filter */}
      <ChartFilter
        filters={filters}
        onFilterChange={handleFilterChange}
        chartType={type}
      />

      {/* Chart Container */}
      <div className="mt-4">
        <div style={{ height: `${height}px` }}>
          {renderChart()}
        </div>
      </div>
    </div>
  );
};

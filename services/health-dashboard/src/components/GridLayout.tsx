import React from 'react';
import { LayoutConfig, WidgetConfig } from '../types';
import { HealthCard } from './HealthCard';
import { MetricsChart } from './MetricsChart';
import { EventFeed } from './EventFeed';
import { HealthCardSkeleton, ChartSkeleton, EventFeedSkeleton } from './SkeletonLoader';

interface GridLayoutProps {
  layout: LayoutConfig;
  health?: any;
  statistics?: any;
  events?: any[];
  loading?: boolean;
  realTime?: boolean;
  onRefresh?: () => void;
}

const WidgetRenderer: React.FC<{ widget: WidgetConfig; props: any }> = ({ widget, props }) => {
  const { type, props: widgetProps } = widget;
  const mergedProps = { ...widgetProps, ...props };

  switch (type) {
    case 'HealthCard':
      return <HealthCard {...mergedProps} />;
    case 'MetricsChart':
      return <MetricsChart {...mergedProps} />;
    case 'EventFeed':
      return <EventFeed {...mergedProps} />;
    default:
      return <div className="p-4 bg-gray-100 rounded">Unknown widget: {type}</div>;
  }
};

const SkeletonRenderer: React.FC<{ widget: WidgetConfig }> = ({ widget }) => {
  const { type } = widget;

  switch (type) {
    case 'HealthCard':
      return <HealthCardSkeleton />;
    case 'MetricsChart':
      return <ChartSkeleton />;
    case 'EventFeed':
      return <EventFeedSkeleton />;
    default:
      return <div className="p-4 bg-gray-100 rounded animate-pulse">Loading...</div>;
  }
};

export const GridLayout: React.FC<GridLayoutProps> = ({
  layout,
  health,
  statistics,
  events = [],
  loading = false,
  realTime = false,
  onRefresh,
}) => {
  const gridStyle = {
    display: 'grid',
    gridTemplateColumns: `repeat(${layout.grid.columns}, 1fr)`,
    gap: `${layout.grid.gap}px`,
    height: '100%',
  };

  const generateEventRateData = () => {
    const labels = [];
    const data = [];
    const now = new Date();
    
    for (let i = 23; i >= 0; i--) {
      const time = new Date(now.getTime() - i * 60 * 60 * 1000);
      labels.push(time.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' }));
      data.push(Math.floor(Math.random() * 100) + 10);
    }
    
    return {
      labels,
      datasets: [{
        label: 'Events per hour',
        data,
        borderColor: 'rgb(59, 130, 246)',
        backgroundColor: 'rgba(59, 130, 246, 0.1)',
        tension: 0.1,
      }],
    };
  };

  const generateErrorRateData = () => {
    const labels = [];
    const data = [];
    const now = new Date();
    
    for (let i = 23; i >= 0; i--) {
      const time = new Date(now.getTime() - i * 60 * 60 * 1000);
      labels.push(time.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' }));
      data.push(Math.floor(Math.random() * 10) + 1);
    }
    
    return {
      labels,
      datasets: [{
        label: 'Errors per hour',
        data,
        backgroundColor: 'rgba(239, 68, 68, 0.8)',
        borderColor: 'rgb(239, 68, 68)',
      }],
    };
  };

  const generateServiceStatusData = () => {
    return {
      labels: ['Healthy', 'Degraded', 'Unhealthy'],
      datasets: [{
        data: [85, 10, 5],
        backgroundColor: [
          'rgba(34, 197, 94, 0.8)',
          'rgba(245, 158, 11, 0.8)',
          'rgba(239, 68, 68, 0.8)',
        ],
        borderColor: [
          'rgb(34, 197, 94)',
          'rgb(245, 158, 11)',
          'rgb(239, 68, 68)',
        ],
        borderWidth: 1,
      }],
    };
  };

  const getWidgetData = (widget: WidgetConfig) => {
    const { type, props } = widget;
    
    switch (type) {
      case 'HealthCard':
        return { health, loading };
      case 'MetricsChart':
        if (props.title?.includes('Event Rate')) {
          return { data: generateEventRateData(), loading, realTime };
        } else if (props.title?.includes('Error Rate')) {
          return { data: generateErrorRateData(), loading, realTime };
        } else if (props.title?.includes('Service Status')) {
          return { data: generateServiceStatusData(), loading, realTime };
        }
        return { data: generateEventRateData(), loading, realTime };
      case 'EventFeed':
        return { events, loading };
      default:
        return {};
    }
  };

  return (
    <div className="dashboard-grid" style={gridStyle}>
      {layout.widgets.map((widget) => {
        const widgetStyle = {
          gridColumn: `${widget.position.x + 1} / span ${widget.position.w}`,
          gridRow: `${widget.position.y + 1} / span ${widget.position.h}`,
        };

        return (
          <div key={widget.id} style={widgetStyle} className="min-h-0">
            {loading ? (
              <SkeletonRenderer widget={widget} />
            ) : (
              <WidgetRenderer
                widget={widget}
                props={getWidgetData(widget)}
              />
            )}
          </div>
        );
      })}
    </div>
  );
};

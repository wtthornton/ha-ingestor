/**
 * MetricsWidget Component
 * 
 * Key metrics widget for customizable dashboard
 * Epic 15.3: Dashboard Customization & Layout
 */

import React from 'react';
import { MetricCard } from '../MetricCard';

interface MetricsWidgetProps {
  health: any;
  darkMode: boolean;
}

export const MetricsWidget: React.FC<MetricsWidgetProps> = ({ health, darkMode }) => {
  return (
    <div className="h-full flex flex-col">
      <h3 className={`text-lg font-semibold mb-3 ${darkMode ? 'text-white' : 'text-gray-900'}`}>
        📊 Key Metrics
      </h3>
      <div className="grid grid-cols-2 gap-3 flex-1">
        <MetricCard
          title="Total Events"
          value={health?.ingestion_service?.event_processing?.total_events || 0}
          unit="events"
          isLive={true}
        />
        <MetricCard
          title="Events/Min"
          value={health?.ingestion_service?.event_processing?.events_per_minute || 0}
          unit="/min"
          isLive={true}
        />
        <MetricCard
          title="Error Rate"
          value={health?.ingestion_service?.event_processing?.error_rate || 0}
          unit="%"
        />
        <MetricCard
          title="API Calls"
          value={health?.ingestion_service?.weather_enrichment?.api_calls || 0}
          unit="calls"
          isLive={true}
        />
      </div>
    </div>
  );
};


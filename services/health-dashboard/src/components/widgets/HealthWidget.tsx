/**
 * HealthWidget Component
 * 
 * System health widget for customizable dashboard
 * Epic 15.3: Dashboard Customization & Layout
 */

import React from 'react';
import { StatusCard } from '../StatusCard';

interface HealthWidgetProps {
  health: any;
  darkMode: boolean;
}

export const HealthWidget: React.FC<HealthWidgetProps> = ({ health, darkMode }) => {
  return (
    <div className="h-full flex flex-col">
      <h3 className={`text-lg font-semibold mb-3 ${darkMode ? 'text-white' : 'text-gray-900'}`}>
        🏥 System Health
      </h3>
      <div className="grid grid-cols-2 gap-3 flex-1">
        <StatusCard
          title="Overall"
          status={health?.overall_status || 'unhealthy'}
          value={health?.overall_status}
        />
        <StatusCard
          title="WebSocket"
          status={health?.ingestion_service?.websocket_connection?.is_connected ? 'connected' : 'disconnected'}
          value={health?.ingestion_service?.websocket_connection?.connection_attempts || 0}
          subtitle="attempts"
        />
        <StatusCard
          title="Processing"
          status={health?.ingestion_service?.event_processing?.status || 'unhealthy'}
          value={health?.ingestion_service?.event_processing?.events_per_minute || 0}
          subtitle="events/min"
        />
        <StatusCard
          title="Database"
          status={health?.ingestion_service?.influxdb_storage?.is_connected ? 'connected' : 'disconnected'}
          value={health?.ingestion_service?.influxdb_storage?.write_errors || 0}
          subtitle="errors"
        />
      </div>
    </div>
  );
};


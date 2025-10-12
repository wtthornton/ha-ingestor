import React, { useState, useEffect } from 'react';
import { AnimatedDependencyGraph } from '../AnimatedDependencyGraph';
import { TabProps } from './types';

export const DependenciesTab: React.FC<TabProps> = ({ darkMode }) => {
  const [services, setServices] = useState<any[]>([]);
  const [realTimeMetrics, setRealTimeMetrics] = useState({
    eventsPerSecond: 0,
    apiCallsActive: 0,
    dataSourcesActive: [],
    lastUpdate: new Date(),
  });

  // Fetch services data for dependencies graph
  useEffect(() => {
    const fetchServices = async () => {
      try {
        const response = await fetch('/api/v1/services');
        if (response.ok) {
          const data = await response.json();
          setServices(data.services || []);
        }
      } catch (error) {
        console.error('Error fetching services:', error);
      }
    };

    fetchServices();
    const interval = setInterval(fetchServices, 30000);
    return () => clearInterval(interval);
  }, []);

  return (
    <AnimatedDependencyGraph 
      services={services}
      darkMode={darkMode}
      realTimeData={realTimeMetrics}
    />
  );
};


import React from 'react';
import { useHealth } from '../../hooks/useHealth';
import { CustomizableDashboard } from '../CustomizableDashboard';
import { TabProps } from './types';

export const CustomTab: React.FC<TabProps> = ({ darkMode }) => {
  const { health } = useHealth(30000);
  
  return <CustomizableDashboard health={health} darkMode={darkMode} />;
};


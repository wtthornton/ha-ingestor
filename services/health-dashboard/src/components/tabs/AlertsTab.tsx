import React from 'react';
import { AlertsPanel } from '../AlertsPanel';
import { TabProps } from './types';

export const AlertsTab: React.FC<TabProps> = ({ darkMode }) => {
  return <AlertsPanel darkMode={darkMode} />;
};


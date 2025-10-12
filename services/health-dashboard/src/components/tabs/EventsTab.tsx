import React from 'react';
import { EventStreamViewer } from '../EventStreamViewer';
import { TabProps } from './types';

export const EventsTab: React.FC<TabProps> = ({ darkMode }) => {
  return <EventStreamViewer darkMode={darkMode} />;
};


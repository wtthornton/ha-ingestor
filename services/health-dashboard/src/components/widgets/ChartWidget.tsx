/**
 * ChartWidget Component
 * 
 * Simple chart widget for customizable dashboard
 * Epic 15.3: Dashboard Customization & Layout
 */

import React from 'react';

interface ChartWidgetProps {
  title: string;
  darkMode: boolean;
}

export const ChartWidget: React.FC<ChartWidgetProps> = ({ title, darkMode }) => {
  // Generate simple mock data
  const data = Array.from({ length: 20 }, (_, i) => ({
    value: Math.random() * 100,
    label: `${i}h`
  }));

  const maxValue = Math.max(...data.map(d => d.value));

  return (
    <div className="h-full flex flex-col">
      <h3 className={`text-lg font-semibold mb-3 ${darkMode ? 'text-white' : 'text-gray-900'}`}>
        📈 {title}
      </h3>
      
      <div className="flex-1 flex items-end gap-1 px-2">
        {data.map((point, idx) => (
          <div
            key={idx}
            className="flex-1 flex flex-col items-center"
          >
            <div
              className={`w-full rounded-t transition-all duration-300 ${
                darkMode ? 'bg-blue-500' : 'bg-blue-600'
              }`}
              style={{ height: `${(point.value / maxValue) * 100}%`, minHeight: '4px' }}
              title={`${point.value.toFixed(1)}`}
            />
          </div>
        ))}
      </div>
      
      <div className="flex justify-between mt-2 text-xs">
        <span className={darkMode ? 'text-gray-400' : 'text-gray-500'}>20h ago</span>
        <span className={darkMode ? 'text-gray-400' : 'text-gray-500'}>Now</span>
      </div>
    </div>
  );
};


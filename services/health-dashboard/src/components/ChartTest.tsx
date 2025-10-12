import React from 'react';

// Simple test component to verify Chart.js is working
export const ChartTest: React.FC = () => {
  try {
    // Try to import Chart.js components
    const { Chart, registerables } = require('chart.js');
    Chart.register(...registerables);
    
    return (
      <div className="p-4">
        <h3 className="text-lg font-bold mb-4">Chart.js Test</h3>
        <div className="bg-green-100 p-4 rounded">
          <p className="text-green-800">✅ Chart.js is working!</p>
          <p className="text-sm text-green-600">Version: {Chart.version || 'Unknown'}</p>
        </div>
      </div>
    );
  } catch (error) {
    return (
      <div className="p-4">
        <h3 className="text-lg font-bold mb-4">Chart.js Test</h3>
        <div className="bg-red-100 p-4 rounded">
          <p className="text-red-800">❌ Chart.js Error:</p>
          <p className="text-sm text-red-600">{error.message}</p>
        </div>
      </div>
    );
  }
};

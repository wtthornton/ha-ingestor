/**
 * Pattern Visualization Chart
 * Interactive charts for pattern analysis
 */

import React from 'react';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  BarElement,
  Title,
  Tooltip,
  Legend,
  ArcElement,
  PointElement,
  LineElement
} from 'chart.js';
import { Bar, Doughnut } from 'react-chartjs-2';
import type { Pattern } from '../types';

ChartJS.register(
  CategoryScale,
  LinearScale,
  BarElement,
  Title,
  Tooltip,
  Legend,
  ArcElement,
  PointElement,
  LineElement
);

interface PatternChartProps {
  patterns: Pattern[];
  darkMode?: boolean;
}

export const PatternTypeChart: React.FC<PatternChartProps> = ({ patterns, darkMode }) => {
  const typeCounts = patterns.reduce((acc, p) => {
    acc[p.pattern_type] = (acc[p.pattern_type] || 0) + 1;
    return acc;
  }, {} as Record<string, number>);

  const data = {
    labels: Object.keys(typeCounts).map(t => t.replace('_', ' ')),
    datasets: [{
      label: 'Pattern Count',
      data: Object.values(typeCounts),
      backgroundColor: [
        'rgba(99, 102, 241, 0.8)',
        'rgba(139, 92, 246, 0.8)',
        'rgba(236, 72, 153, 0.8)',
      ],
      borderColor: [
        'rgba(99, 102, 241, 1)',
        'rgba(139, 92, 246, 1)',
        'rgba(236, 72, 153, 1)',
      ],
      borderWidth: 2,
    }]
  };

  const options = {
    responsive: true,
    plugins: {
      legend: {
        labels: {
          color: darkMode ? '#e5e7eb' : '#374151'
        }
      },
      title: {
        display: true,
        text: 'Patterns by Type',
        color: darkMode ? '#ffffff' : '#111827',
        font: { size: 16, weight: 'bold' as const }
      }
    },
    scales: {
      y: {
        beginAtZero: true,
        ticks: { color: darkMode ? '#9ca3af' : '#6b7280' },
        grid: { color: darkMode ? '#374151' : '#e5e7eb' }
      },
      x: {
        ticks: { color: darkMode ? '#9ca3af' : '#6b7280' },
        grid: { color: darkMode ? '#374151' : '#e5e7eb' }
      }
    }
  };

  return <Bar data={data} options={options} />;
};

export const ConfidenceDistributionChart: React.FC<PatternChartProps> = ({ patterns, darkMode }) => {
  const ranges = {
    'High (90-100%)': patterns.filter(p => p.confidence >= 0.9).length,
    'Medium (70-90%)': patterns.filter(p => p.confidence >= 0.7 && p.confidence < 0.9).length,
    'Low (<70%)': patterns.filter(p => p.confidence < 0.7).length,
  };

  const data = {
    labels: Object.keys(ranges),
    datasets: [{
      data: Object.values(ranges),
      backgroundColor: [
        'rgba(16, 185, 129, 0.8)',
        'rgba(245, 158, 11, 0.8)',
        'rgba(239, 68, 68, 0.8)',
      ],
      borderColor: [
        'rgba(16, 185, 129, 1)',
        'rgba(245, 158, 11, 1)',
        'rgba(239, 68, 68, 1)',
      ],
      borderWidth: 2,
    }]
  };

  const options = {
    responsive: true,
    plugins: {
      legend: {
        labels: {
          color: darkMode ? '#e5e7eb' : '#374151'
        }
      },
      title: {
        display: true,
        text: 'Confidence Distribution',
        color: darkMode ? '#ffffff' : '#111827',
        font: { size: 16, weight: 'bold' as const }
      }
    }
  };

  return <Doughnut data={data} options={options} />;
};

export const TopDevicesChart: React.FC<PatternChartProps> = ({ patterns, darkMode }) => {
  const deviceCounts = patterns.reduce((acc, p) => {
    acc[p.device_id] = (acc[p.device_id] || 0) + 1;
    return acc;
  }, {} as Record<string, number>);

  const sorted = Object.entries(deviceCounts)
    .sort(([, a], [, b]) => b - a)
    .slice(0, 10);

  const data = {
    labels: sorted.map(([device]) => device.split('.')[1] || device),
    datasets: [{
      label: 'Pattern Count',
      data: sorted.map(([, count]) => count),
      backgroundColor: 'rgba(99, 102, 241, 0.8)',
      borderColor: 'rgba(99, 102, 241, 1)',
      borderWidth: 2,
    }]
  };

  const options = {
    responsive: true,
    indexAxis: 'y' as const,
    plugins: {
      legend: {
        display: false
      },
      title: {
        display: true,
        text: 'Top 10 Devices by Pattern Count',
        color: darkMode ? '#ffffff' : '#111827',
        font: { size: 16, weight: 'bold' as const }
      }
    },
    scales: {
      y: {
        ticks: { color: darkMode ? '#9ca3af' : '#6b7280' },
        grid: { display: false }
      },
      x: {
        beginAtZero: true,
        ticks: { color: darkMode ? '#9ca3af' : '#6b7280' },
        grid: { color: darkMode ? '#374151' : '#e5e7eb' }
      }
    }
  };

  return <Bar data={data} options={options} />;
};


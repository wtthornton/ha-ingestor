/**
 * Pattern Visualization Chart
 * Interactive charts for pattern analysis
 */

import React, { useState, useEffect } from 'react';
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
import api from '../services/api';

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
  const [deviceNames, setDeviceNames] = useState<Record<string, string>>({});
  const [loading, setLoading] = useState(true);

  const deviceCounts = patterns.reduce((acc, p) => {
    acc[p.device_id] = (acc[p.device_id] || 0) + 1;
    return acc;
  }, {} as Record<string, number>);

  const sorted = Object.entries(deviceCounts)
    .sort(([, a], [, b]) => b - a)
    .slice(0, 10);

  // Load device names when component mounts or patterns change
  useEffect(() => {
    const loadDeviceNames = async () => {
      if (sorted.length === 0) {
        setLoading(false);
        return;
      }

      try {
        const deviceIds = sorted.map(([deviceId]) => deviceId);
        const names = await api.getDeviceNames(deviceIds);
        setDeviceNames(names);
      } catch (error) {
        console.error('Failed to load device names:', error);
        // Fallback to more meaningful names
        const fallbackNames: Record<string, string> = {};
        const deviceIds = sorted.map(([deviceId]) => deviceId);
        deviceIds.forEach((id: string) => {
          if (id.includes('+')) {
            // Co-occurrence pattern
            const parts = id.split('+');
            if (parts.length === 2) {
              fallbackNames[id] = `Co-occurrence (${parts[0].substring(0, 8)}... + ${parts[1].substring(0, 8)}...)`;
            } else {
              fallbackNames[id] = `Pattern (${id.substring(0, 20)}...)`;
            }
          } else {
            fallbackNames[id] = id.length > 20 ? `${id.substring(0, 20)}...` : id;
          }
        });
        setDeviceNames(fallbackNames);
      } finally {
        setLoading(false);
      }
    };

    loadDeviceNames();
  }, [patterns]);

  const data = {
    labels: sorted.map(([deviceId]) => deviceNames[deviceId] || deviceId),
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

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className={`text-center ${darkMode ? 'text-gray-400' : 'text-gray-600'}`}>
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto mb-2"></div>
          Loading device names...
        </div>
      </div>
    );
  }

  return <Bar data={data} options={options} />;
};


import React from 'react';

interface MetricCardProps {
  title: string;
  value: string | number;
  unit?: string;
  trend?: 'up' | 'down' | 'stable';
  className?: string;
}

const getTrendIcon = (trend?: string) => {
  switch (trend) {
    case 'up':
      return '📈';
    case 'down':
      return '📉';
    case 'stable':
      return '➡️';
    default:
      return null;
  }
};

export const MetricCard: React.FC<MetricCardProps> = ({
  title,
  value,
  unit,
  trend,
  className = ''
}) => {
  return (
    <div className={`bg-white rounded-lg shadow-sm border p-6 ${className}`}>
      <div className="flex items-center justify-between mb-2">
        <h3 className="text-sm font-medium text-gray-900">{title}</h3>
        {trend && (
          <span className="text-lg">{getTrendIcon(trend)}</span>
        )}
      </div>
      
      <div className="flex items-baseline">
        <p className="text-3xl font-bold text-gray-900">
          {typeof value === 'number' ? value.toLocaleString() : value}
        </p>
        {unit && (
          <p className="ml-2 text-sm text-gray-500">{unit}</p>
        )}
      </div>
    </div>
  );
};

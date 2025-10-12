import React, { useEffect, useState } from 'react';

interface MetricCardProps {
  title: string;
  value: string | number;
  unit?: string;
  trend?: 'up' | 'down' | 'stable';
  className?: string;
  isLive?: boolean; // Pulse animation for live data
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
  className = '',
  isLive = false
}) => {
  const [displayValue, setDisplayValue] = useState(value);
  const [isAnimating, setIsAnimating] = useState(false);

  // Number counting animation when value changes
  useEffect(() => {
    if (typeof value === 'number' && typeof displayValue === 'number' && value !== displayValue) {
      setIsAnimating(true);
      const duration = 500; // ms
      const steps = 20;
      const stepValue = (value - displayValue) / steps;
      let currentStep = 0;

      const timer = setInterval(() => {
        currentStep++;
        if (currentStep === steps) {
          setDisplayValue(value);
          clearInterval(timer);
          setIsAnimating(false);
        } else {
          setDisplayValue(prev => typeof prev === 'number' ? prev + stepValue : value);
        }
      }, duration / steps);

      return () => clearInterval(timer);
    } else if (value !== displayValue) {
      setDisplayValue(value);
    }
  }, [value, displayValue]);

  return (
    <div className={`card-base card-hover ${isLive ? 'live-pulse' : ''} ${className}`}>
      <div className="flex items-center justify-between mb-2">
        <h3 className="text-sm font-medium text-gray-900 dark:text-gray-300">{title}</h3>
        {trend && (
          <span className="text-lg icon-entrance">{getTrendIcon(trend)}</span>
        )}
        {isLive && (
          <span className="live-indicator"></span>
        )}
      </div>
      
      <div className="flex items-baseline">
        <p className={`text-3xl font-bold text-gray-900 dark:text-white ${isAnimating ? 'number-counter' : ''}`}>
          {typeof displayValue === 'number' ? Math.round(displayValue).toLocaleString() : displayValue}
        </p>
        {unit && (
          <p className="ml-2 text-sm text-gray-500 dark:text-gray-400">{unit}</p>
        )}
      </div>
    </div>
  );
};

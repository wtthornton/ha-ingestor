import React from 'react';
import { render, screen } from '@testing-library/react';
import { 
  SkeletonLoader, 
  HealthCardSkeleton, 
  ChartSkeleton, 
  EventFeedSkeleton 
} from '../../src/components/SkeletonLoader';

describe('SkeletonLoader', () => {
  test('renders with default props', () => {
    render(<SkeletonLoader />);
    
    const skeleton = document.querySelector('.animate-pulse');
    expect(skeleton).toBeInTheDocument();
    expect(skeleton).toHaveClass('animate-pulse');
  });

  test('renders with custom className', () => {
    render(<SkeletonLoader className="custom-class" />);
    
    const skeleton = document.querySelector('.animate-pulse.custom-class');
    expect(skeleton).toBeInTheDocument();
    expect(skeleton).toHaveClass('animate-pulse', 'custom-class');
  });

  test('renders correct number of lines', () => {
    render(<SkeletonLoader lines={5} />);
    
    const lines = document.querySelectorAll('.animate-pulse div[class*="bg-gray-200"]');
    expect(lines).toHaveLength(5);
  });

  test('renders with custom height', () => {
    render(<SkeletonLoader height="h-6" />);
    
    const lines = document.querySelectorAll('.animate-pulse div[class*="h-6"]');
    expect(lines.length).toBeGreaterThan(0);
  });

  test('applies correct width classes to lines', () => {
    render(<SkeletonLoader lines={3} />);
    
    const lines = document.querySelectorAll('.animate-pulse div[class*="bg-gray-200"]');
    
    // First line should be w-3/4
    expect(lines[0]).toHaveClass('w-3/4');
    // Second line should be w-1/2
    expect(lines[1]).toHaveClass('w-1/2');
    // Last line should be w-5/6
    expect(lines[2]).toHaveClass('w-5/6');
  });
});

describe('HealthCardSkeleton', () => {
  test('renders health card skeleton', () => {
    render(<HealthCardSkeleton />);
    
    const skeleton = document.querySelector('.bg-white.rounded-lg.shadow-md.p-6');
    expect(skeleton).toBeInTheDocument();
    expect(skeleton).toHaveClass('bg-white', 'rounded-lg', 'shadow-md', 'p-6');
  });

  test('contains animated pulse effect', () => {
    render(<HealthCardSkeleton />);
    
    const skeleton = document.querySelector('.animate-pulse');
    expect(skeleton).toBeInTheDocument();
    expect(skeleton).toHaveClass('animate-pulse');
  });

  test('renders title skeleton', () => {
    render(<HealthCardSkeleton />);
    
    const titleSkeleton = document.querySelector('.animate-pulse div[class*="h-6"]');
    expect(titleSkeleton).toBeInTheDocument();
    expect(titleSkeleton).toHaveClass('h-6', 'bg-gray-200', 'rounded', 'w-1/3');
  });

  test('renders metrics skeletons', () => {
    render(<HealthCardSkeleton />);
    
    const metricsSkeletons = document.querySelectorAll('.animate-pulse div[class*="text-center"]');
    expect(metricsSkeletons).toHaveLength(3);
  });
});

describe('ChartSkeleton', () => {
  test('renders chart skeleton with default height', () => {
    render(<ChartSkeleton />);
    
    const skeleton = document.querySelector('.bg-white.rounded-lg.shadow-md.p-6');
    expect(skeleton).toBeInTheDocument();
    expect(skeleton).toHaveClass('bg-white', 'rounded-lg', 'shadow-md', 'p-6');
  });

  test('renders chart skeleton with custom height', () => {
    render(<ChartSkeleton height={400} />);
    
    const chartArea = document.querySelector('div[style*="height: 400px"]');
    expect(chartArea).toBeInTheDocument();
  });

  test('contains animated pulse effect', () => {
    render(<ChartSkeleton />);
    
    const skeleton = document.querySelector('.animate-pulse');
    expect(skeleton).toBeInTheDocument();
    expect(skeleton).toHaveClass('animate-pulse');
  });

  test('renders title skeleton', () => {
    render(<ChartSkeleton />);
    
    const titleSkeleton = document.querySelector('.animate-pulse div[class*="h-6"]');
    expect(titleSkeleton).toBeInTheDocument();
    expect(titleSkeleton).toHaveClass('h-6', 'bg-gray-200', 'rounded', 'w-1/4');
  });
});

describe('EventFeedSkeleton', () => {
  test('renders event feed skeleton', () => {
    const { container } = render(<EventFeedSkeleton />);
    
    const skeleton = container.firstChild as HTMLElement;
    expect(skeleton).toHaveClass('bg-white', 'rounded-lg', 'shadow-md', 'p-6');
  });

  test('contains animated pulse effect', () => {
    const { container } = render(<EventFeedSkeleton />);
    
    const pulseElement = container.querySelector('.animate-pulse');
    expect(pulseElement).toBeInTheDocument();
  });

  test('renders title skeleton', () => {
    const { container } = render(<EventFeedSkeleton />);
    
    const titleSkeleton = container.querySelector('div[class*="h-6"]');
    expect(titleSkeleton).toHaveClass('h-6', 'bg-gray-200', 'rounded', 'w-1/4');
  });

  test('renders event item skeletons', () => {
    const { container } = render(<EventFeedSkeleton />);
    
    const eventSkeletons = container.querySelectorAll('div[class*="flex items-center space-x-3"]');
    expect(eventSkeletons).toHaveLength(5);
  });

  test('renders event indicator skeletons', () => {
    const { container } = render(<EventFeedSkeleton />);
    
    const indicatorSkeletons = container.querySelectorAll('div[class*="h-3 w-3 bg-gray-200 rounded-full"]');
    expect(indicatorSkeletons).toHaveLength(5);
  });
});

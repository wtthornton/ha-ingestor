import { useState, useEffect } from 'react';

export interface MobileDetectionState {
  isMobile: boolean;
  isTablet: boolean;
  isDesktop: boolean;
  screenWidth: number;
  screenHeight: number;
  orientation: 'portrait' | 'landscape';
  deviceType: 'mobile' | 'tablet' | 'desktop';
  userAgent: string;
  isTouchDevice: boolean;
}

export const useMobileDetection = (): MobileDetectionState => {
  const [state, setState] = useState<MobileDetectionState>(() => {
    const width = typeof window !== 'undefined' ? window.innerWidth : 1024;
    const height = typeof window !== 'undefined' ? window.innerHeight : 768;
    const userAgent = typeof navigator !== 'undefined' ? navigator.userAgent : '';
    
    return {
      isMobile: width <= 768,
      isTablet: width > 768 && width <= 1024,
      isDesktop: width > 1024,
      screenWidth: width,
      screenHeight: height,
      orientation: height > width ? 'portrait' : 'landscape',
      deviceType: width <= 768 ? 'mobile' : width <= 1024 ? 'tablet' : 'desktop',
      userAgent,
      isTouchDevice: 'ontouchstart' in window || navigator.maxTouchPoints > 0,
    };
  });

  useEffect(() => {
    const updateState = () => {
      const width = window.innerWidth;
      const height = window.innerHeight;
      const userAgent = navigator.userAgent;
      
      setState({
        isMobile: width <= 768,
        isTablet: width > 768 && width <= 1024,
        isDesktop: width > 1024,
        screenWidth: width,
        screenHeight: height,
        orientation: height > width ? 'portrait' : 'landscape',
        deviceType: width <= 768 ? 'mobile' : width <= 1024 ? 'tablet' : 'desktop',
        userAgent,
        isTouchDevice: 'ontouchstart' in window || navigator.maxTouchPoints > 0,
      });
    };

    // Initial check
    updateState();

    // Listen for resize events
    window.addEventListener('resize', updateState);
    
    // Listen for orientation changes
    window.addEventListener('orientationchange', () => {
      // Small delay to ensure the orientation change is complete
      setTimeout(updateState, 100);
    });

    return () => {
      window.removeEventListener('resize', updateState);
      window.removeEventListener('orientationchange', updateState);
    };
  }, []);

  return state;
};

// Utility functions for mobile detection
export const isMobileDevice = (userAgent?: string): boolean => {
  const ua = userAgent || (typeof navigator !== 'undefined' ? navigator.userAgent : '');
  
  return /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(ua);
};

export const isTabletDevice = (userAgent?: string): boolean => {
  const ua = userAgent || (typeof navigator !== 'undefined' ? navigator.userAgent : '');
  
  return /iPad|Android(?=.*\bMobile\b)/i.test(ua) || 
         (window.innerWidth > 768 && window.innerWidth <= 1024);
};

export const isTouchDevice = (): boolean => {
  return 'ontouchstart' in window || 
         navigator.maxTouchPoints > 0 || 
         (navigator as any).msMaxTouchPoints > 0;
};

export const getDevicePixelRatio = (): number => {
  return typeof window !== 'undefined' ? window.devicePixelRatio || 1 : 1;
};

export const isHighDPIDevice = (): boolean => {
  return getDevicePixelRatio() > 1.5;
};

export const isRetinaDevice = (): boolean => {
  return getDevicePixelRatio() >= 2;
};

// Breakpoint utilities
export const useBreakpoint = () => {
  const { screenWidth } = useMobileDetection();
  
  return {
    isXs: screenWidth < 480,
    isSm: screenWidth >= 480 && screenWidth < 640,
    isMd: screenWidth >= 640 && screenWidth < 768,
    isLg: screenWidth >= 768 && screenWidth < 1024,
    isXl: screenWidth >= 1024 && screenWidth < 1280,
    is2Xl: screenWidth >= 1280,
  };
};

// Performance utilities for mobile
export const useMobilePerformance = () => {
  const { isMobile, isTouchDevice } = useMobileDetection();
  
  return {
    shouldReduceAnimations: isMobile && window.matchMedia('(prefers-reduced-motion: reduce)').matches,
    shouldOptimizeImages: isMobile || isHighDPIDevice(),
    shouldLazyLoad: isMobile,
    shouldUseVirtualScrolling: isMobile,
    shouldDebounceScroll: isMobile,
  };
};

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { renderHook, act } from '@testing-library/react';
import { 
  useMobileDetection, 
  isMobileDevice, 
  isTabletDevice, 
  isTouchDevice,
  getDevicePixelRatio,
  isHighDPIDevice,
  isRetinaDevice,
  useBreakpoint,
  useMobilePerformance
} from '../../src/hooks/useMobileDetection';

// Mock window and navigator
const mockWindow = {
  innerWidth: 1024,
  innerHeight: 768,
  devicePixelRatio: 1,
  matchMedia: vi.fn(),
};

const mockNavigator = {
  userAgent: 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
  maxTouchPoints: 0,
};

describe('useMobileDetection', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    
    // Reset mocks
    Object.defineProperty(window, 'innerWidth', {
      writable: true,
      value: 1024,
    });
    Object.defineProperty(window, 'innerHeight', {
      writable: true,
      value: 768,
    });
    Object.defineProperty(window, 'devicePixelRatio', {
      writable: true,
      value: 1,
    });
    
    Object.defineProperty(navigator, 'userAgent', {
      writable: true,
      value: 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    });
    Object.defineProperty(navigator, 'maxTouchPoints', {
      writable: true,
      value: 0,
    });
    
    // Mock matchMedia
    window.matchMedia = vi.fn().mockImplementation((query) => ({
      matches: false,
      media: query,
      onchange: null,
      addListener: vi.fn(),
      removeListener: vi.fn(),
      addEventListener: vi.fn(),
      removeEventListener: vi.fn(),
      dispatchEvent: vi.fn(),
    }));
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  describe('useMobileDetection', () => {
    it('should detect desktop device', () => {
      const { result } = renderHook(() => useMobileDetection());

      expect(result.current.isMobile).toBe(false);
      expect(result.current.isTablet).toBe(false);
      expect(result.current.isDesktop).toBe(true);
      expect(result.current.deviceType).toBe('desktop');
      expect(result.current.orientation).toBe('landscape');
    });

    it('should detect mobile device', () => {
      // Mock mobile dimensions
      Object.defineProperty(window, 'innerWidth', { value: 375 });
      Object.defineProperty(window, 'innerHeight', { value: 667 });
      
      const { result } = renderHook(() => useMobileDetection());

      expect(result.current.isMobile).toBe(true);
      expect(result.current.isTablet).toBe(false);
      expect(result.current.isDesktop).toBe(false);
      expect(result.current.deviceType).toBe('mobile');
      expect(result.current.orientation).toBe('portrait');
    });

    it('should detect tablet device', () => {
      // Mock tablet dimensions
      Object.defineProperty(window, 'innerWidth', { value: 768 });
      Object.defineProperty(window, 'innerHeight', { value: 1024 });
      
      const { result } = renderHook(() => useMobileDetection());

      expect(result.current.isMobile).toBe(false);
      expect(result.current.isTablet).toBe(true);
      expect(result.current.isDesktop).toBe(false);
      expect(result.current.deviceType).toBe('tablet');
      expect(result.current.orientation).toBe('portrait');
    });

    it('should detect touch device', () => {
      Object.defineProperty(navigator, 'maxTouchPoints', { value: 5 });
      
      const { result } = renderHook(() => useMobileDetection());

      expect(result.current.isTouchDevice).toBe(true);
    });

    it('should update on resize', () => {
      const { result } = renderHook(() => useMobileDetection());

      expect(result.current.screenWidth).toBe(1024);

      // Simulate resize
      Object.defineProperty(window, 'innerWidth', { value: 375 });
      
      act(() => {
        window.dispatchEvent(new Event('resize'));
      });

      expect(result.current.screenWidth).toBe(375);
      expect(result.current.isMobile).toBe(true);
    });

    it('should update on orientation change', () => {
      const { result } = renderHook(() => useMobileDetection());

      expect(result.current.orientation).toBe('landscape');

      // Simulate orientation change
      Object.defineProperty(window, 'innerWidth', { value: 375 });
      Object.defineProperty(window, 'innerHeight', { value: 667 });
      
      act(() => {
        window.dispatchEvent(new Event('orientationchange'));
      });

      // Wait for the timeout
      act(() => {
        vi.advanceTimersByTime(100);
      });

      expect(result.current.orientation).toBe('portrait');
    });
  });

  describe('isMobileDevice', () => {
    it('should detect mobile user agent', () => {
      const mobileUserAgent = 'Mozilla/5.0 (iPhone; CPU iPhone OS 14_0 like Mac OS X)';
      expect(isMobileDevice(mobileUserAgent)).toBe(true);
    });

    it('should detect Android mobile', () => {
      const androidUserAgent = 'Mozilla/5.0 (Linux; Android 10; SM-G975F)';
      expect(isMobileDevice(androidUserAgent)).toBe(true);
    });

    it('should not detect desktop user agent', () => {
      const desktopUserAgent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36';
      expect(isMobileDevice(desktopUserAgent)).toBe(false);
    });
  });

  describe('isTabletDevice', () => {
    it('should detect iPad user agent', () => {
      const iPadUserAgent = 'Mozilla/5.0 (iPad; CPU OS 14_0 like Mac OS X)';
      expect(isTabletDevice(iPadUserAgent)).toBe(true);
    });

    it('should detect Android tablet', () => {
      const androidTabletUserAgent = 'Mozilla/5.0 (Linux; Android 10; SM-T870)';
      expect(isTabletDevice(androidTabletUserAgent)).toBe(true);
    });

    it('should not detect mobile user agent', () => {
      const mobileUserAgent = 'Mozilla/5.0 (iPhone; CPU iPhone OS 14_0 like Mac OS X)';
      expect(isTabletDevice(mobileUserAgent)).toBe(false);
    });
  });

  describe('isTouchDevice', () => {
    it('should detect touch device', () => {
      Object.defineProperty(navigator, 'maxTouchPoints', { value: 5 });
      expect(isTouchDevice()).toBe(true);
    });

    it('should not detect non-touch device', () => {
      Object.defineProperty(navigator, 'maxTouchPoints', { value: 0 });
      expect(isTouchDevice()).toBe(false);
    });
  });

  describe('getDevicePixelRatio', () => {
    it('should return device pixel ratio', () => {
      Object.defineProperty(window, 'devicePixelRatio', { value: 2 });
      expect(getDevicePixelRatio()).toBe(2);
    });

    it('should return 1 as fallback', () => {
      Object.defineProperty(window, 'devicePixelRatio', { value: undefined });
      expect(getDevicePixelRatio()).toBe(1);
    });
  });

  describe('isHighDPIDevice', () => {
    it('should detect high DPI device', () => {
      Object.defineProperty(window, 'devicePixelRatio', { value: 2 });
      expect(isHighDPIDevice()).toBe(true);
    });

    it('should not detect low DPI device', () => {
      Object.defineProperty(window, 'devicePixelRatio', { value: 1 });
      expect(isHighDPIDevice()).toBe(false);
    });
  });

  describe('isRetinaDevice', () => {
    it('should detect retina device', () => {
      Object.defineProperty(window, 'devicePixelRatio', { value: 2 });
      expect(isRetinaDevice()).toBe(true);
    });

    it('should detect high resolution retina device', () => {
      Object.defineProperty(window, 'devicePixelRatio', { value: 3 });
      expect(isRetinaDevice()).toBe(true);
    });

    it('should not detect non-retina device', () => {
      Object.defineProperty(window, 'devicePixelRatio', { value: 1 });
      expect(isRetinaDevice()).toBe(false);
    });
  });

  describe('useBreakpoint', () => {
    it('should detect xs breakpoint', () => {
      Object.defineProperty(window, 'innerWidth', { value: 400 });
      
      const { result } = renderHook(() => useBreakpoint());

      expect(result.current.isXs).toBe(true);
      expect(result.current.isSm).toBe(false);
      expect(result.current.isMd).toBe(false);
      expect(result.current.isLg).toBe(false);
      expect(result.current.isXl).toBe(false);
      expect(result.current.is2Xl).toBe(false);
    });

    it('should detect sm breakpoint', () => {
      Object.defineProperty(window, 'innerWidth', { value: 500 });
      
      const { result } = renderHook(() => useBreakpoint());

      expect(result.current.isXs).toBe(false);
      expect(result.current.isSm).toBe(true);
      expect(result.current.isMd).toBe(false);
    });

    it('should detect md breakpoint', () => {
      Object.defineProperty(window, 'innerWidth', { value: 700 });
      
      const { result } = renderHook(() => useBreakpoint());

      expect(result.current.isXs).toBe(false);
      expect(result.current.isSm).toBe(false);
      expect(result.current.isMd).toBe(true);
    });

    it('should detect lg breakpoint', () => {
      Object.defineProperty(window, 'innerWidth', { value: 900 });
      
      const { result } = renderHook(() => useBreakpoint());

      expect(result.current.isXs).toBe(false);
      expect(result.current.isSm).toBe(false);
      expect(result.current.isMd).toBe(false);
      expect(result.current.isLg).toBe(true);
    });

    it('should detect xl breakpoint', () => {
      Object.defineProperty(window, 'innerWidth', { value: 1200 });
      
      const { result } = renderHook(() => useBreakpoint());

      expect(result.current.isXs).toBe(false);
      expect(result.current.isSm).toBe(false);
      expect(result.current.isMd).toBe(false);
      expect(result.current.isLg).toBe(false);
      expect(result.current.isXl).toBe(true);
      expect(result.current.is2Xl).toBe(false);
    });

    it('should detect 2xl breakpoint', () => {
      Object.defineProperty(window, 'innerWidth', { value: 1400 });
      
      const { result } = renderHook(() => useBreakpoint());

      expect(result.current.isXs).toBe(false);
      expect(result.current.isSm).toBe(false);
      expect(result.current.isMd).toBe(false);
      expect(result.current.isLg).toBe(false);
      expect(result.current.isXl).toBe(false);
      expect(result.current.is2Xl).toBe(true);
    });
  });

  describe('useMobilePerformance', () => {
    it('should return mobile performance settings for mobile device', () => {
      Object.defineProperty(window, 'innerWidth', { value: 375 });
      Object.defineProperty(navigator, 'maxTouchPoints', { value: 5 });
      
      const { result } = renderHook(() => useMobilePerformance());

      expect(result.current.shouldReduceAnimations).toBe(false);
      expect(result.current.shouldOptimizeImages).toBe(true);
      expect(result.current.shouldLazyLoad).toBe(true);
      expect(result.current.shouldUseVirtualScrolling).toBe(true);
      expect(result.current.shouldDebounceScroll).toBe(true);
    });

    it('should return desktop performance settings for desktop device', () => {
      Object.defineProperty(window, 'innerWidth', { value: 1024 });
      Object.defineProperty(navigator, 'maxTouchPoints', { value: 0 });
      
      const { result } = renderHook(() => useMobilePerformance());

      expect(result.current.shouldReduceAnimations).toBe(false);
      expect(result.current.shouldOptimizeImages).toBe(false);
      expect(result.current.shouldLazyLoad).toBe(false);
      expect(result.current.shouldUseVirtualScrolling).toBe(false);
      expect(result.current.shouldDebounceScroll).toBe(false);
    });

    it('should detect reduced motion preference', () => {
      Object.defineProperty(window, 'innerWidth', { value: 375 });
      Object.defineProperty(navigator, 'maxTouchPoints', { value: 5 });
      
      // Mock matchMedia to return reduced motion preference
      window.matchMedia = vi.fn().mockImplementation((query) => ({
        matches: query === '(prefers-reduced-motion: reduce)',
        media: query,
        onchange: null,
        addListener: vi.fn(),
        removeListener: vi.fn(),
        addEventListener: vi.fn(),
        removeEventListener: vi.fn(),
        dispatchEvent: vi.fn(),
      }));
      
      const { result } = renderHook(() => useMobilePerformance());

      expect(result.current.shouldReduceAnimations).toBe(true);
    });
  });
});

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { renderHook, act } from '@testing-library/react';
import { useSwipeGesture, usePinchGesture, useTapGesture, useTouchGestures } from '../../src/hooks/useTouchGestures';

// Mock touch events
const createTouchEvent = (type: string, touches: Array<{ clientX: number; clientY: number }>) => {
  return new TouchEvent(type, {
    touches: touches.map(touch => ({
      clientX: touch.clientX,
      clientY: touch.clientY,
    })) as any,
    targetTouches: touches.map(touch => ({
      clientX: touch.clientX,
      clientY: touch.clientY,
    })) as any,
    changedTouches: touches.map(touch => ({
      clientX: touch.clientX,
      clientY: touch.clientY,
    })) as any,
  });
};

describe('useTouchGestures', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('useSwipeGesture', () => {
    it('should detect left swipe', () => {
      const onSwipeLeft = vi.fn();
      const onSwipeRight = vi.fn();
      
      const { result } = renderHook(() => 
        useSwipeGesture({ onSwipeLeft, onSwipeRight })
      );

      const { touchHandlers } = result.current;

      // Simulate touch start
      const touchStart = createTouchEvent('touchstart', [{ clientX: 100, clientY: 50 }]);
      act(() => {
        touchHandlers.onTouchStart(touchStart);
      });

      // Simulate touch move (swipe left)
      const touchMove = createTouchEvent('touchmove', [{ clientX: 30, clientY: 50 }]);
      act(() => {
        touchHandlers.onTouchMove(touchMove);
      });

      // Simulate touch end
      act(() => {
        touchHandlers.onTouchEnd();
      });

      expect(onSwipeLeft).toHaveBeenCalled();
      expect(onSwipeRight).not.toHaveBeenCalled();
    });

    it('should detect right swipe', () => {
      const onSwipeLeft = vi.fn();
      const onSwipeRight = vi.fn();
      
      const { result } = renderHook(() => 
        useSwipeGesture({ onSwipeLeft, onSwipeRight })
      );

      const { touchHandlers } = result.current;

      // Simulate touch start
      const touchStart = createTouchEvent('touchstart', [{ clientX: 100, clientY: 50 }]);
      act(() => {
        touchHandlers.onTouchStart(touchStart);
      });

      // Simulate touch move (swipe right)
      const touchMove = createTouchEvent('touchmove', [{ clientX: 170, clientY: 50 }]);
      act(() => {
        touchHandlers.onTouchMove(touchMove);
      });

      // Simulate touch end
      act(() => {
        touchHandlers.onTouchEnd();
      });

      expect(onSwipeRight).toHaveBeenCalled();
      expect(onSwipeLeft).not.toHaveBeenCalled();
    });

    it('should detect up swipe', () => {
      const onSwipeUp = vi.fn();
      const onSwipeDown = vi.fn();
      
      const { result } = renderHook(() => 
        useSwipeGesture({ onSwipeUp, onSwipeDown })
      );

      const { touchHandlers } = result.current;

      // Simulate touch start
      const touchStart = createTouchEvent('touchstart', [{ clientX: 100, clientY: 100 }]);
      act(() => {
        touchHandlers.onTouchStart(touchStart);
      });

      // Simulate touch move (swipe up)
      const touchMove = createTouchEvent('touchmove', [{ clientX: 100, clientY: 30 }]);
      act(() => {
        touchHandlers.onTouchMove(touchMove);
      });

      // Simulate touch end
      act(() => {
        touchHandlers.onTouchEnd();
      });

      expect(onSwipeUp).toHaveBeenCalled();
      expect(onSwipeDown).not.toHaveBeenCalled();
    });

    it('should detect down swipe', () => {
      const onSwipeUp = vi.fn();
      const onSwipeDown = vi.fn();
      
      const { result } = renderHook(() => 
        useSwipeGesture({ onSwipeUp, onSwipeDown })
      );

      const { touchHandlers } = result.current;

      // Simulate touch start
      const touchStart = createTouchEvent('touchstart', [{ clientX: 100, clientY: 100 }]);
      act(() => {
        touchHandlers.onTouchStart(touchStart);
      });

      // Simulate touch move (swipe down)
      const touchMove = createTouchEvent('touchmove', [{ clientX: 100, clientY: 170 }]);
      act(() => {
        touchHandlers.onTouchMove(touchMove);
      });

      // Simulate touch end
      act(() => {
        touchHandlers.onTouchEnd();
      });

      expect(onSwipeDown).toHaveBeenCalled();
      expect(onSwipeUp).not.toHaveBeenCalled();
    });

    it('should not trigger swipe for small movements', () => {
      const onSwipeLeft = vi.fn();
      const onSwipeRight = vi.fn();
      
      const { result } = renderHook(() => 
        useSwipeGesture({ onSwipeLeft, onSwipeRight }, { minSwipeDistance: 100 })
      );

      const { touchHandlers } = result.current;

      // Simulate touch start
      const touchStart = createTouchEvent('touchstart', [{ clientX: 100, clientY: 50 }]);
      act(() => {
        touchHandlers.onTouchStart(touchStart);
      });

      // Simulate small movement
      const touchMove = createTouchEvent('touchmove', [{ clientX: 120, clientY: 50 }]);
      act(() => {
        touchHandlers.onTouchMove(touchMove);
      });

      // Simulate touch end
      act(() => {
        touchHandlers.onTouchEnd();
      });

      expect(onSwipeLeft).not.toHaveBeenCalled();
      expect(onSwipeRight).not.toHaveBeenCalled();
    });

    it('should update gesture state correctly', () => {
      const { result } = renderHook(() => 
        useSwipeGesture({})
      );

      const { touchHandlers, gestureState } = result.current;

      expect(gestureState.isTouching).toBe(false);
      expect(gestureState.touchStart).toBe(null);

      // Simulate touch start
      const touchStart = createTouchEvent('touchstart', [{ clientX: 100, clientY: 50 }]);
      act(() => {
        touchHandlers.onTouchStart(touchStart);
      });

      expect(gestureState.isTouching).toBe(true);
      expect(gestureState.touchStart).toEqual({ x: 100, y: 50 });
    });
  });

  describe('usePinchGesture', () => {
    it('should detect pinch start', () => {
      const onPinchStart = vi.fn();
      const onPinchMove = vi.fn();
      const onPinchEnd = vi.fn();
      
      const { result } = renderHook(() => 
        usePinchGesture({ onPinchStart, onPinchMove, onPinchEnd })
      );

      const { touchHandlers } = result.current;

      // Simulate two-finger touch start
      const touchStart = createTouchEvent('touchstart', [
        { clientX: 100, clientY: 100 },
        { clientX: 200, clientY: 100 }
      ]);
      
      act(() => {
        touchHandlers.onTouchStart(touchStart);
      });

      expect(onPinchStart).toHaveBeenCalledWith(1);
    });

    it('should detect pinch move', () => {
      const onPinchStart = vi.fn();
      const onPinchMove = vi.fn();
      const onPinchEnd = vi.fn();
      
      const { result } = renderHook(() => 
        usePinchGesture({ onPinchStart, onPinchMove, onPinchEnd })
      );

      const { touchHandlers } = result.current;

      // Simulate pinch start
      const touchStart = createTouchEvent('touchstart', [
        { clientX: 100, clientY: 100 },
        { clientX: 200, clientY: 100 }
      ]);
      
      act(() => {
        touchHandlers.onTouchStart(touchStart);
      });

      // Simulate pinch move (zoom out)
      const touchMove = createTouchEvent('touchmove', [
        { clientX: 90, clientY: 100 },
        { clientX: 210, clientY: 100 }
      ]);
      
      act(() => {
        touchHandlers.onTouchMove(touchMove);
      });

      expect(onPinchMove).toHaveBeenCalled();
    });

    it('should detect pinch end', () => {
      const onPinchStart = vi.fn();
      const onPinchMove = vi.fn();
      const onPinchEnd = vi.fn();
      
      const { result } = renderHook(() => 
        usePinchGesture({ onPinchStart, onPinchMove, onPinchEnd })
      );

      const { touchHandlers } = result.current;

      // Simulate pinch start
      const touchStart = createTouchEvent('touchstart', [
        { clientX: 100, clientY: 100 },
        { clientX: 200, clientY: 100 }
      ]);
      
      act(() => {
        touchHandlers.onTouchStart(touchStart);
      });

      // Simulate touch end
      act(() => {
        touchHandlers.onTouchEnd();
      });

      expect(onPinchEnd).toHaveBeenCalled();
    });
  });

  describe('useTapGesture', () => {
    it('should detect single tap', () => {
      const onTap = vi.fn();
      
      const { result } = renderHook(() => 
        useTapGesture(onTap)
      );

      const { touchHandlers } = result.current;

      // Simulate touch end (tap)
      const touchEnd = createTouchEvent('touchend', [{ clientX: 100, clientY: 50 }]);
      
      act(() => {
        touchHandlers.onTouchEnd(touchEnd);
      });

      expect(onTap).toHaveBeenCalledWith(touchEnd);
    });

    it('should detect double tap', () => {
      const onTap = vi.fn();
      
      const { result } = renderHook(() => 
        useTapGesture(onTap, { doubleTap: true })
      );

      const { touchHandlers } = result.current;

      // First tap
      const touchEnd1 = createTouchEvent('touchend', [{ clientX: 100, clientY: 50 }]);
      act(() => {
        touchHandlers.onTouchEnd(touchEnd1);
      });

      expect(onTap).not.toHaveBeenCalled();

      // Second tap (within time limit)
      const touchEnd2 = createTouchEvent('touchend', [{ clientX: 100, clientY: 50 }]);
      act(() => {
        touchHandlers.onTouchEnd(touchEnd2);
      });

      expect(onTap).toHaveBeenCalledWith(touchEnd2);
    });
  });

  describe('useTouchGestures', () => {
    it('should combine multiple gestures', () => {
      const swipeCallbacks = { onSwipeLeft: vi.fn() };
      const pinchCallbacks = { onPinchStart: vi.fn() };
      const tapCallback = vi.fn();
      
      const { result } = renderHook(() => 
        useTouchGestures({
          swipe: { callbacks: swipeCallbacks },
          pinch: { callbacks: pinchCallbacks },
          tap: { callback: tapCallback },
        })
      );

      const { touchHandlers } = result.current;

      expect(touchHandlers.onTouchStart).toBeDefined();
      expect(touchHandlers.onTouchMove).toBeDefined();
      expect(touchHandlers.onTouchEnd).toBeDefined();
    });

    it('should handle individual gestures', () => {
      const swipeCallbacks = { onSwipeLeft: vi.fn() };
      
      const { result } = renderHook(() => 
        useTouchGestures({
          swipe: { callbacks: swipeCallbacks },
        })
      );

      const { swipeGesture } = result.current;

      expect(swipeGesture).toBeDefined();
      expect(swipeGesture?.gestureState).toBeDefined();
    });
  });
});

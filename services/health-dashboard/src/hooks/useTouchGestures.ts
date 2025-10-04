import { useState, useCallback, useRef, useEffect } from 'react';

export interface TouchGestureOptions {
  minSwipeDistance?: number;
  maxSwipeTime?: number;
  preventDefault?: boolean;
  passive?: boolean;
}

export interface SwipeGestureCallbacks {
  onSwipeLeft?: () => void;
  onSwipeRight?: () => void;
  onSwipeUp?: () => void;
  onSwipeDown?: () => void;
  onSwipeStart?: (touch: Touch) => void;
  onSwipeEnd?: (direction: 'left' | 'right' | 'up' | 'down' | null) => void;
}

export interface PinchGestureCallbacks {
  onPinchStart?: (scale: number) => void;
  onPinchMove?: (scale: number, center: { x: number; y: number }) => void;
  onPinchEnd?: (scale: number) => void;
}

export interface TouchGestureState {
  isTouching: boolean;
  touchStart: { x: number; y: number } | null;
  touchCurrent: { x: number; y: number } | null;
  swipeDirection: 'left' | 'right' | 'up' | 'down' | null;
  isSwipeValid: boolean;
}

/**
 * Hook for handling swipe gestures
 */
export const useSwipeGesture = (
  callbacks: SwipeGestureCallbacks,
  options: TouchGestureOptions = {}
) => {
  const {
    minSwipeDistance = 50,
    maxSwipeTime = 300,
    preventDefault = true,
    passive = false,
  } = options;

  const [gestureState, setGestureState] = useState<TouchGestureState>({
    isTouching: false,
    touchStart: null,
    touchCurrent: null,
    swipeDirection: null,
    isSwipeValid: false,
  });

  const touchStartTime = useRef<number>(0);
  const touchStartPos = useRef<{ x: number; y: number } | null>(null);

  const onTouchStart = useCallback((e: TouchEvent) => {
    if (preventDefault) e.preventDefault();
    
    const touch = e.touches[0];
    const startPos = { x: touch.clientX, y: touch.clientY };
    
    touchStartTime.current = Date.now();
    touchStartPos.current = startPos;
    
    setGestureState({
      isTouching: true,
      touchStart: startPos,
      touchCurrent: startPos,
      swipeDirection: null,
      isSwipeValid: false,
    });

    callbacks.onSwipeStart?.(touch);
  }, [callbacks, preventDefault]);

  const onTouchMove = useCallback((e: TouchEvent) => {
    if (!gestureState.isTouching || !touchStartPos.current) return;
    
    const touch = e.touches[0];
    const currentPos = { x: touch.clientX, y: touch.clientY };
    
    const deltaX = currentPos.x - touchStartPos.current.x;
    const deltaY = currentPos.y - touchStartPos.current.y;
    
    const absDeltaX = Math.abs(deltaX);
    const absDeltaY = Math.abs(deltaY);
    
    let swipeDirection: 'left' | 'right' | 'up' | 'down' | null = null;
    let isSwipeValid = false;
    
    if (absDeltaX > absDeltaY && absDeltaX > minSwipeDistance) {
      swipeDirection = deltaX > 0 ? 'right' : 'left';
      isSwipeValid = true;
    } else if (absDeltaY > absDeltaX && absDeltaY > minSwipeDistance) {
      swipeDirection = deltaY > 0 ? 'down' : 'up';
      isSwipeValid = true;
    }
    
    setGestureState(prev => ({
      ...prev,
      touchCurrent: currentPos,
      swipeDirection,
      isSwipeValid,
    }));
  }, [gestureState.isTouching, minSwipeDistance]);

  const onTouchEnd = useCallback(() => {
    if (!gestureState.isTouching || !touchStartPos.current) return;
    
    const touchDuration = Date.now() - touchStartTime.current;
    const isValidSwipe = gestureState.isSwipeValid && touchDuration <= maxSwipeTime;
    
    setGestureState({
      isTouching: false,
      touchStart: null,
      touchCurrent: null,
      swipeDirection: null,
      isSwipeValid: false,
    });
    
    if (isValidSwipe && gestureState.swipeDirection) {
      switch (gestureState.swipeDirection) {
        case 'left':
          callbacks.onSwipeLeft?.();
          break;
        case 'right':
          callbacks.onSwipeRight?.();
          break;
        case 'up':
          callbacks.onSwipeUp?.();
          break;
        case 'down':
          callbacks.onSwipeDown?.();
          break;
      }
    }
    
    callbacks.onSwipeEnd?.(isValidSwipe ? gestureState.swipeDirection : null);
    
    touchStartPos.current = null;
  }, [gestureState, callbacks, maxSwipeTime]);

  return {
    gestureState,
    touchHandlers: {
      onTouchStart,
      onTouchMove,
      onTouchEnd,
    },
  };
};

/**
 * Hook for handling pinch gestures (zoom)
 */
export const usePinchGesture = (
  callbacks: PinchGestureCallbacks,
  options: TouchGestureOptions = {}
) => {
  const { preventDefault = true } = options;
  
  const [pinchState, setPinchState] = useState({
    isPinching: false,
    initialDistance: 0,
    currentDistance: 0,
    scale: 1,
  });

  const getDistance = useCallback((touch1: Touch, touch2: Touch) => {
    const dx = touch1.clientX - touch2.clientX;
    const dy = touch1.clientY - touch2.clientY;
    return Math.sqrt(dx * dx + dy * dy);
  }, []);

  const getCenter = useCallback((touch1: Touch, touch2: Touch) => {
    return {
      x: (touch1.clientX + touch2.clientX) / 2,
      y: (touch1.clientY + touch2.clientY) / 2,
    };
  }, []);

  const onTouchStart = useCallback((e: TouchEvent) => {
    if (preventDefault) e.preventDefault();
    
    if (e.touches.length === 2) {
      const distance = getDistance(e.touches[0], e.touches[1]);
      const center = getCenter(e.touches[0], e.touches[1]);
      
      setPinchState({
        isPinching: true,
        initialDistance: distance,
        currentDistance: distance,
        scale: 1,
      });
      
      callbacks.onPinchStart?.(1);
    }
  }, [callbacks, preventDefault, getDistance, getCenter]);

  const onTouchMove = useCallback((e: TouchEvent) => {
    if (!pinchState.isPinching || e.touches.length !== 2) return;
    
    const distance = getDistance(e.touches[0], e.touches[1]);
    const center = getCenter(e.touches[0], e.touches[1]);
    const scale = distance / pinchState.initialDistance;
    
    setPinchState(prev => ({
      ...prev,
      currentDistance: distance,
      scale,
    }));
    
    callbacks.onPinchMove?.(scale, center);
  }, [pinchState.isPinching, pinchState.initialDistance, callbacks, getDistance, getCenter]);

  const onTouchEnd = useCallback(() => {
    if (pinchState.isPinching) {
      callbacks.onPinchEnd?.(pinchState.scale);
      
      setPinchState({
        isPinching: false,
        initialDistance: 0,
        currentDistance: 0,
        scale: 1,
      });
    }
  }, [pinchState.isPinching, pinchState.scale, callbacks]);

  return {
    pinchState,
    touchHandlers: {
      onTouchStart,
      onTouchMove,
      onTouchEnd,
    },
  };
};

/**
 * Hook for handling tap gestures
 */
export const useTapGesture = (
  onTap: (event: TouchEvent) => void,
  options: { doubleTap?: boolean; maxTapTime?: number } = {}
) => {
  const { doubleTap = false, maxTapTime = 300 } = options;
  
  const [tapState, setTapState] = useState({
    tapCount: 0,
    lastTapTime: 0,
  });

  const onTouchEnd = useCallback((e: TouchEvent) => {
    const now = Date.now();
    const timeSinceLastTap = now - tapState.lastTapTime;
    
    if (doubleTap) {
      if (timeSinceLastTap <= maxTapTime) {
        setTapState(prev => ({ ...prev, tapCount: prev.tapCount + 1 }));
        if (tapState.tapCount === 1) {
          onTap(e);
          setTapState({ tapCount: 0, lastTapTime: now });
        }
      } else {
        setTapState({ tapCount: 1, lastTapTime: now });
      }
    } else {
      if (timeSinceLastTap <= maxTapTime) {
        onTap(e);
      }
      setTapState({ tapCount: 0, lastTapTime: now });
    }
  }, [onTap, doubleTap, maxTapTime, tapState]);

  return {
    tapState,
    touchHandlers: {
      onTouchEnd,
    },
  };
};

/**
 * Hook for combining multiple touch gestures
 */
export const useTouchGestures = (
  gestures: {
    swipe?: { callbacks: SwipeGestureCallbacks; options?: TouchGestureOptions };
    pinch?: { callbacks: PinchGestureCallbacks; options?: TouchGestureOptions };
    tap?: { callback: (event: TouchEvent) => void; options?: { doubleTap?: boolean; maxTapTime?: number } };
  }
) => {
  const swipeGesture = gestures.swipe ? useSwipeGesture(gestures.swipe.callbacks, gestures.swipe.options) : null;
  const pinchGesture = gestures.pinch ? usePinchGesture(gestures.pinch.callbacks, gestures.pinch.options) : null;
  const tapGesture = gestures.tap ? useTapGesture(gestures.tap.callback, gestures.tap.options) : null;

  const combinedHandlers = {
    onTouchStart: (e: TouchEvent) => {
      swipeGesture?.touchHandlers.onTouchStart(e);
      pinchGesture?.touchHandlers.onTouchStart(e);
    },
    onTouchMove: (e: TouchEvent) => {
      swipeGesture?.touchHandlers.onTouchMove(e);
      pinchGesture?.touchHandlers.onTouchMove(e);
    },
    onTouchEnd: (e: TouchEvent) => {
      swipeGesture?.touchHandlers.onTouchEnd();
      pinchGesture?.touchHandlers.onTouchEnd();
      tapGesture?.touchHandlers.onTouchEnd(e);
    },
  };

  return {
    swipeGesture,
    pinchGesture,
    tapGesture,
    touchHandlers: combinedHandlers,
  };
};

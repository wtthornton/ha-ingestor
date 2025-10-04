import { useState, useEffect, useRef, useCallback } from 'react';

export interface StatusUpdate {
  id: string;
  timestamp: Date;
  status: 'healthy' | 'warning' | 'error' | 'unknown';
  message: string;
  data?: any;
}

export interface StatusUpdateOptions {
  enableAnimations?: boolean;
  animationDuration?: number;
  maxUpdates?: number;
  onStatusChange?: (update: StatusUpdate) => void;
}

export const useStatusUpdates = (options: StatusUpdateOptions = {}) => {
  const {
    enableAnimations = true,
    animationDuration = 300,
    maxUpdates = 50,
    onStatusChange,
  } = options;

  const [updates, setUpdates] = useState<StatusUpdate[]>([]);
  const [isUpdating, setIsUpdating] = useState(false);
  const [lastUpdate, setLastUpdate] = useState<Date | null>(null);
  const animationRef = useRef<number | null>(null);

  const addUpdate = useCallback((update: StatusUpdate) => {
    setIsUpdating(true);
    
    setUpdates(prev => {
      const newUpdates = [update, ...prev].slice(0, maxUpdates);
      return newUpdates;
    });
    
    setLastUpdate(update.timestamp);
    onStatusChange?.(update);
    
    if (enableAnimations) {
      // Clear any existing animation
      if (animationRef.current) {
        clearTimeout(animationRef.current);
      }
      
      // Set animation timeout
      animationRef.current = window.setTimeout(() => {
        setIsUpdating(false);
      }, animationDuration);
    } else {
      setIsUpdating(false);
    }
  }, [enableAnimations, animationDuration, maxUpdates, onStatusChange]);

  const clearUpdates = useCallback(() => {
    setUpdates([]);
    setLastUpdate(null);
  }, []);

  const getLatestStatus = useCallback(() => {
    return updates[0]?.status || 'unknown';
  }, [updates]);

  const getStatusCount = useCallback((status: StatusUpdate['status']) => {
    return updates.filter(update => update.status === status).length;
  }, [updates]);

  const getRecentUpdates = useCallback((count: number = 10) => {
    return updates.slice(0, count);
  }, [updates]);

  // Cleanup animation timeout on unmount
  useEffect(() => {
    return () => {
      if (animationRef.current) {
        clearTimeout(animationRef.current);
      }
    };
  }, []);

  return {
    updates,
    isUpdating,
    lastUpdate,
    addUpdate,
    clearUpdates,
    getLatestStatus,
    getStatusCount,
    getRecentUpdates,
  };
};

// Status Animation Hook
export const useStatusAnimation = (
  status: 'healthy' | 'warning' | 'error' | 'unknown',
  options: { duration?: number; enablePulse?: boolean } = {}
) => {
  const { duration = 1000, enablePulse = true } = options;
  const [isAnimating, setIsAnimating] = useState(false);
  const [animationKey, setAnimationKey] = useState(0);

  useEffect(() => {
    if (enablePulse) {
      setIsAnimating(true);
      setAnimationKey(prev => prev + 1);
      
      const timeout = setTimeout(() => {
        setIsAnimating(false);
      }, duration);
      
      return () => clearTimeout(timeout);
    }
  }, [status, duration, enablePulse]);

  const getAnimationClasses = () => {
    if (!isAnimating) return '';
    
    switch (status) {
      case 'healthy':
        return 'animate-pulse-glow';
      case 'warning':
        return 'animate-bounce-subtle';
      case 'error':
        return 'animate-pulse';
      case 'unknown':
        return 'animate-fade-in';
      default:
        return '';
    }
  };

  return {
    isAnimating,
    animationKey,
    animationClasses: getAnimationClasses(),
  };
};

// Real-time Status Monitor Hook
export interface StatusMonitorOptions {
  checkInterval?: number;
  timeout?: number;
  retryAttempts?: number;
  onStatusChange?: (status: 'healthy' | 'warning' | 'error' | 'unknown') => void;
}

export const useStatusMonitor = (
  checkFunction: () => Promise<{ status: 'healthy' | 'warning' | 'error' | 'unknown'; message: string }>,
  options: StatusMonitorOptions = {}
) => {
  const {
    checkInterval = 30000,
    timeout = 10000,
    retryAttempts = 3,
    onStatusChange,
  } = options;

  const [currentStatus, setCurrentStatus] = useState<'healthy' | 'warning' | 'error' | 'unknown'>('unknown');
  const [lastCheck, setLastCheck] = useState<Date | null>(null);
  const [isChecking, setIsChecking] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const intervalRef = useRef<NodeJS.Timeout | null>(null);
  const timeoutRef = useRef<NodeJS.Timeout | null>(null);

  const performCheck = useCallback(async () => {
    if (isChecking) return;
    
    setIsChecking(true);
    setError(null);
    
    try {
      // Set timeout for the check
      const timeoutPromise = new Promise<never>((_, reject) => {
        timeoutRef.current = setTimeout(() => {
          reject(new Error('Status check timeout'));
        }, timeout);
      });
      
      const checkPromise = checkFunction();
      const result = await Promise.race([checkPromise, timeoutPromise]);
      
      // Clear timeout
      if (timeoutRef.current) {
        clearTimeout(timeoutRef.current);
        timeoutRef.current = null;
      }
      
      setCurrentStatus(result.status);
      setLastCheck(new Date());
      onStatusChange?.(result.status);
      
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Unknown error';
      setError(errorMessage);
      setCurrentStatus('error');
      setLastCheck(new Date());
      onStatusChange?.('error');
    } finally {
      setIsChecking(false);
    }
  }, [checkFunction, timeout, isChecking, onStatusChange]);

  const startMonitoring = useCallback(() => {
    if (intervalRef.current) return;
    
    // Perform initial check
    performCheck();
    
    // Set up interval
    intervalRef.current = setInterval(performCheck, checkInterval);
  }, [performCheck, checkInterval]);

  const stopMonitoring = useCallback(() => {
    if (intervalRef.current) {
      clearInterval(intervalRef.current);
      intervalRef.current = null;
    }
    
    if (timeoutRef.current) {
      clearTimeout(timeoutRef.current);
      timeoutRef.current = null;
    }
  }, []);

  const forceCheck = useCallback(() => {
    performCheck();
  }, [performCheck]);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      stopMonitoring();
    };
  }, [stopMonitoring]);

  return {
    currentStatus,
    lastCheck,
    isChecking,
    error,
    startMonitoring,
    stopMonitoring,
    forceCheck,
  };
};

// Status Transition Hook
export const useStatusTransition = (
  fromStatus: 'healthy' | 'warning' | 'error' | 'unknown',
  toStatus: 'healthy' | 'warning' | 'error' | 'unknown',
  options: { duration?: number; easing?: string } = {}
) => {
  const { duration = 500, easing = 'ease-in-out' } = options;
  const [isTransitioning, setIsTransitioning] = useState(false);
  const [transitionProgress, setTransitionProgress] = useState(0);

  useEffect(() => {
    if (fromStatus === toStatus) return;
    
    setIsTransitioning(true);
    setTransitionProgress(0);
    
    const startTime = Date.now();
    
    const animate = () => {
      const elapsed = Date.now() - startTime;
      const progress = Math.min(elapsed / duration, 1);
      
      setTransitionProgress(progress);
      
      if (progress < 1) {
        requestAnimationFrame(animate);
      } else {
        setIsTransitioning(false);
      }
    };
    
    requestAnimationFrame(animate);
  }, [fromStatus, toStatus, duration]);

  const getTransitionStyle = () => {
    if (!isTransitioning) return {};
    
    return {
      transition: `all ${duration}ms ${easing}`,
      opacity: 0.5 + (transitionProgress * 0.5),
      transform: `scale(${0.95 + (transitionProgress * 0.05)})`,
    };
  };

  return {
    isTransitioning,
    transitionProgress,
    transitionStyle: getTransitionStyle(),
  };
};

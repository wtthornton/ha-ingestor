import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import { LayoutConfig, LayoutState, LayoutType } from '../types';
import { LAYOUT_CONFIGS, DEFAULT_LAYOUT, getAllLayouts } from '../config/layouts';

interface LayoutContextType {
  layoutState: LayoutState;
  setCurrentLayout: (layoutId: string) => void;
  getCurrentLayoutConfig: () => LayoutConfig | null;
  isTransitioning: boolean;
}

const LayoutContext = createContext<LayoutContextType | undefined>(undefined);

interface LayoutProviderProps {
  children: ReactNode;
}

export const LayoutProvider: React.FC<LayoutProviderProps> = ({ children }) => {
  const [currentLayout, setCurrentLayoutState] = useState<string>(DEFAULT_LAYOUT);
  const [isTransitioning, setIsTransitioning] = useState(false);

  // Load layout preference from localStorage
  useEffect(() => {
    const savedLayout = localStorage.getItem('dashboard-layout');
    if (savedLayout && LAYOUT_CONFIGS[savedLayout]) {
      setCurrentLayoutState(savedLayout);
    }
  }, []);

  const setCurrentLayout = (layoutId: string) => {
    if (!LAYOUT_CONFIGS[layoutId]) {
      console.warn(`Layout ${layoutId} not found`);
      return;
    }

    setIsTransitioning(true);
    
    // Save to localStorage
    localStorage.setItem('dashboard-layout', layoutId);
    
    // Update state with transition effect
    setTimeout(() => {
      setCurrentLayoutState(layoutId);
      setIsTransitioning(false);
    }, 150);
  };

  const getCurrentLayoutConfig = (): LayoutConfig | null => {
    return LAYOUT_CONFIGS[currentLayout] || null;
  };

  const layoutState: LayoutState = {
    currentLayout,
    availableLayouts: getAllLayouts(),
    isTransitioning,
  };

  const value: LayoutContextType = {
    layoutState,
    setCurrentLayout,
    getCurrentLayoutConfig,
    isTransitioning,
  };

  return (
    <LayoutContext.Provider value={value}>
      {children}
    </LayoutContext.Provider>
  );
};

export const useLayout = (): LayoutContextType => {
  const context = useContext(LayoutContext);
  if (context === undefined) {
    throw new Error('useLayout must be used within a LayoutProvider');
  }
  return context;
};

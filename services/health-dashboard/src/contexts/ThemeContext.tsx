import React, { createContext, useContext, useReducer, useEffect, ReactNode } from 'react';

// Theme types
export type Theme = 'light' | 'dark' | 'system';

export interface ThemeState {
  theme: Theme;
  resolvedTheme: 'light' | 'dark';
  systemTheme: 'light' | 'dark';
}

export interface ThemeContextType {
  theme: Theme;
  resolvedTheme: 'light' | 'dark';
  setTheme: (theme: Theme) => void;
  toggleTheme: () => void;
}

// Action types
type ThemeAction =
  | { type: 'SET_THEME'; payload: Theme }
  | { type: 'SET_SYSTEM_THEME'; payload: 'light' | 'dark' }
  | { type: 'RESOLVE_THEME' };

// Initial state
const initialState: ThemeState = {
  theme: 'system',
  resolvedTheme: 'light',
  systemTheme: 'light',
};

// Reducer
function themeReducer(state: ThemeState, action: ThemeAction): ThemeState {
  switch (action.type) {
    case 'SET_THEME':
      const newTheme = action.payload;
      const resolvedTheme = newTheme === 'system' ? state.systemTheme : newTheme;
      return {
        ...state,
        theme: newTheme,
        resolvedTheme,
      };

    case 'SET_SYSTEM_THEME':
      const newSystemTheme = action.payload;
      const newResolvedTheme = state.theme === 'system' ? newSystemTheme : state.resolvedTheme;
      return {
        ...state,
        systemTheme: newSystemTheme,
        resolvedTheme: newResolvedTheme,
      };

    case 'RESOLVE_THEME':
      return {
        ...state,
        resolvedTheme: state.theme === 'system' ? state.systemTheme : state.theme,
      };

    default:
      return state;
  }
}

// Context
const ThemeContext = createContext<ThemeContextType | undefined>(undefined);

// Provider component
interface ThemeProviderProps {
  children: ReactNode;
}

export function ThemeProvider({ children }: ThemeProviderProps) {
  const [state, dispatch] = useReducer(themeReducer, initialState);

  // Load theme from localStorage on mount
  useEffect(() => {
    const savedTheme = localStorage.getItem('theme') as Theme;
    if (savedTheme && ['light', 'dark', 'system'].includes(savedTheme)) {
      dispatch({ type: 'SET_THEME', payload: savedTheme });
    }
  }, []);

  // Detect system theme preference
  useEffect(() => {
    const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)');
    const systemTheme = mediaQuery.matches ? 'dark' : 'light';
    
    dispatch({ type: 'SET_SYSTEM_THEME', payload: systemTheme });

    const handleChange = (e: MediaQueryListEvent) => {
      const newSystemTheme = e.matches ? 'dark' : 'light';
      dispatch({ type: 'SET_SYSTEM_THEME', payload: newSystemTheme });
    };

    mediaQuery.addEventListener('change', handleChange);
    return () => mediaQuery.removeEventListener('change', handleChange);
  }, []);

  // Apply theme to document
  useEffect(() => {
    const root = document.documentElement;
    
    // Remove existing theme classes
    root.classList.remove('light', 'dark');
    root.removeAttribute('data-theme');
    
    // Apply new theme
    root.setAttribute('data-theme', state.resolvedTheme);
    root.classList.add(state.resolvedTheme);
    
    // Update meta theme-color for mobile browsers
    const metaThemeColor = document.querySelector('meta[name="theme-color"]');
    if (metaThemeColor) {
      metaThemeColor.setAttribute('content', state.resolvedTheme === 'dark' ? '#111827' : '#ffffff');
    }
  }, [state.resolvedTheme]);

  // Context value
  const contextValue: ThemeContextType = {
    theme: state.theme,
    resolvedTheme: state.resolvedTheme,
    setTheme: (theme: Theme) => {
      dispatch({ type: 'SET_THEME', payload: theme });
      localStorage.setItem('theme', theme);
    },
    toggleTheme: () => {
      const newTheme = state.resolvedTheme === 'light' ? 'dark' : 'light';
      dispatch({ type: 'SET_THEME', payload: newTheme });
      localStorage.setItem('theme', newTheme);
    },
  };

  return (
    <ThemeContext.Provider value={contextValue}>
      {children}
    </ThemeContext.Provider>
  );
}

// Hook to use theme context
export function useTheme(): ThemeContextType {
  const context = useContext(ThemeContext);
  if (context === undefined) {
    throw new Error('useTheme must be used within a ThemeProvider');
  }
  return context;
}

// Hook for theme-aware styling
export function useThemeAware() {
  const { resolvedTheme } = useTheme();
  
  return {
    isDark: resolvedTheme === 'dark',
    isLight: resolvedTheme === 'light',
    theme: resolvedTheme,
  };
}

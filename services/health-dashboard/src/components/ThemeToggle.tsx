import React from 'react';
import { SunIcon, MoonIcon, ComputerDesktopIcon } from '@heroicons/react/24/outline';
import { useTheme } from '../contexts/ThemeContext';

interface ThemeToggleProps {
  className?: string;
  showLabel?: boolean;
  variant?: 'button' | 'select' | 'toggle';
}

export const ThemeToggle: React.FC<ThemeToggleProps> = ({ 
  className = '', 
  showLabel = false,
  variant = 'button' 
}) => {
  const { theme, resolvedTheme, setTheme, toggleTheme } = useTheme();

  const getThemeIcon = (themeType: string) => {
    switch (themeType) {
      case 'light':
        return <SunIcon className="h-4 w-4" />;
      case 'dark':
        return <MoonIcon className="h-4 w-4" />;
      case 'system':
        return <ComputerDesktopIcon className="h-4 w-4" />;
      default:
        return <SunIcon className="h-4 w-4" />;
    }
  };

  const getThemeLabel = (themeType: string) => {
    switch (themeType) {
      case 'light':
        return 'Light';
      case 'dark':
        return 'Dark';
      case 'system':
        return 'System';
      default:
        return 'Light';
    }
  };

  if (variant === 'select') {
    return (
      <div className={`relative ${className}`}>
        <select
          value={theme}
          onChange={(e) => setTheme(e.target.value as any)}
          className="
            appearance-none bg-design-surface border border-design-border rounded-design-md px-3 py-2 pr-8
            text-design-text text-sm font-medium
            focus:outline-none focus:ring-2 focus:ring-design-border-focus focus:border-design-border-focus
            hover:bg-design-surface-hover transition-colors duration-design-fast
          "
          aria-label="Select theme"
        >
          <option value="light">Light</option>
          <option value="dark">Dark</option>
          <option value="system">System</option>
        </select>
        <div className="absolute inset-y-0 right-0 flex items-center pr-2 pointer-events-none">
          {getThemeIcon(resolvedTheme)}
        </div>
      </div>
    );
  }

  if (variant === 'toggle') {
    return (
      <button
        onClick={toggleTheme}
        className={`
          relative inline-flex items-center justify-center
          w-12 h-6 rounded-full transition-colors duration-design-normal
          focus:outline-none focus:ring-2 focus:ring-design-border-focus focus:ring-offset-2
          ${resolvedTheme === 'dark' 
            ? 'bg-design-primary' 
            : 'bg-design-border'
          }
          ${className}
        `}
        aria-label={`Switch to ${resolvedTheme === 'dark' ? 'light' : 'dark'} theme`}
      >
        <span
          className={`
            absolute left-1 top-1 w-4 h-4 bg-white rounded-full shadow-md
            transform transition-transform duration-design-normal
            ${resolvedTheme === 'dark' ? 'translate-x-6' : 'translate-x-0'}
          `}
        >
          {resolvedTheme === 'dark' ? (
            <MoonIcon className="h-3 w-3 text-design-primary-dark m-0.5" />
          ) : (
            <SunIcon className="h-3 w-3 text-design-warning m-0.5" />
          )}
        </span>
      </button>
    );
  }

  // Default button variant
  return (
    <div className={`flex items-center space-x-2 ${className}`}>
      <button
        onClick={toggleTheme}
        className="
          flex items-center space-x-2 px-3 py-2 rounded-design-md
          bg-design-surface border border-design-border
          text-design-text text-sm font-medium
          hover:bg-design-surface-hover hover:border-design-border-hover
          focus:outline-none focus:ring-2 focus:ring-design-border-focus focus:border-design-border-focus
          transition-all duration-design-fast
        "
        aria-label={`Switch to ${resolvedTheme === 'dark' ? 'light' : 'dark'} theme`}
      >
        {getThemeIcon(resolvedTheme)}
        {showLabel && (
          <span>{getThemeLabel(resolvedTheme)}</span>
        )}
      </button>
      
      {showLabel && (
        <div className="flex space-x-1">
          {(['light', 'dark', 'system'] as const).map((themeOption) => (
            <button
              key={themeOption}
              onClick={() => setTheme(themeOption)}
              className={`
                px-2 py-1 text-xs rounded-design-sm transition-colors duration-design-fast
                ${theme === themeOption
                  ? 'bg-design-primary text-design-text-inverse'
                  : 'text-design-text-secondary hover:text-design-text hover:bg-design-surface-hover'
                }
              `}
            >
              {getThemeLabel(themeOption)}
            </button>
          ))}
        </div>
      )}
    </div>
  );
};

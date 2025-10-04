import React from 'react';
import { Link, NavLink } from 'react-router-dom';
import { ThemeToggle } from './ThemeToggle';
import { NotificationBell } from './NotificationBell';
import { useThemeAware } from '../contexts/ThemeContext';

export const Navigation: React.FC = () => {
  const { isDark } = useThemeAware();

  return (
    <nav className={`
      ${isDark 
        ? 'bg-design-background-secondary border-design-border' 
        : 'bg-design-background-secondary border-design-border'
      } 
      border-b shadow-design-sm p-4 transition-colors duration-design-normal
    `}>
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between items-center">
          <div className="flex items-center space-x-8">
            <Link 
              to="/" 
              className="text-xl font-bold text-design-text hover:text-design-text-secondary transition-colors duration-design-fast"
            >
              Health Dashboard
            </Link>
            
            <div className="flex space-x-1">
              <NavLink 
                to="/" 
                className={({ isActive }) => 
                  `px-3 py-2 rounded-design-md text-sm font-medium transition-all duration-design-fast ${
                    isActive 
                      ? 'bg-design-primary text-design-text-inverse shadow-design-sm' 
                      : 'text-design-text-secondary hover:text-design-text hover:bg-design-surface-hover'
                  }`
                }
              >
                Dashboard
              </NavLink>
              <NavLink 
                to="/monitoring" 
                className={({ isActive }) => 
                  `px-3 py-2 rounded-design-md text-sm font-medium transition-all duration-design-fast ${
                    isActive 
                      ? 'bg-design-primary text-design-text-inverse shadow-design-sm' 
                      : 'text-design-text-secondary hover:text-design-text hover:bg-design-surface-hover'
                  }`
                }
              >
                Monitoring
              </NavLink>
              <NavLink 
                to="/settings" 
                className={({ isActive }) => 
                  `px-3 py-2 rounded-design-md text-sm font-medium transition-all duration-design-fast ${
                    isActive 
                      ? 'bg-design-primary text-design-text-inverse shadow-design-sm' 
                      : 'text-design-text-secondary hover:text-design-text hover:bg-design-surface-hover'
                  }`
                }
              >
                Settings
              </NavLink>
            </div>
          </div>
          
          <div className="flex items-center space-x-4">
            <div className="text-sm text-design-text-secondary">
              Home Assistant Ingestor
            </div>
            
            {/* Theme Toggle */}
            <ThemeToggle variant="toggle" />
            
            {/* Notification Bell */}
            <NotificationBell />
          </div>
        </div>
      </div>
    </nav>
  );
};

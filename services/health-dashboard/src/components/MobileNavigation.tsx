import React, { useState, useEffect } from 'react';
import { Link, useLocation } from 'react-router-dom';
import { 
  HomeIcon, 
  ChartBarIcon, 
  CogIcon, 
  BellIcon,
  Bars3Icon,
  XMarkIcon
} from '@heroicons/react/24/outline';
import { ThemeToggle } from './ThemeToggle';
import { NotificationBell } from './NotificationBell';
import { useThemeAware } from '../contexts/ThemeContext';
import { useTouchGestures } from '../hooks/useTouchGestures';

interface MobileNavigationProps {
  className?: string;
}

export const MobileNavigation: React.FC<MobileNavigationProps> = ({ className = '' }) => {
  const location = useLocation();
  const { isDark } = useThemeAware();
  const [isMenuOpen, setIsMenuOpen] = useState(false);
  const [isBottomNavVisible, setIsBottomNavVisible] = useState(true);
  const [lastScrollY, setLastScrollY] = useState(0);

  // Handle scroll to show/hide bottom navigation
  useEffect(() => {
    const handleScroll = () => {
      const currentScrollY = window.scrollY;
      
      if (currentScrollY > lastScrollY && currentScrollY > 100) {
        // Scrolling down
        setIsBottomNavVisible(false);
      } else {
        // Scrolling up
        setIsBottomNavVisible(true);
      }
      
      setLastScrollY(currentScrollY);
    };

    window.addEventListener('scroll', handleScroll, { passive: true });
    return () => window.removeEventListener('scroll', handleScroll);
  }, [lastScrollY]);

  // Touch gestures for navigation
  const { touchHandlers } = useTouchGestures({
    swipe: {
      callbacks: {
        onSwipeUp: () => setIsBottomNavVisible(true),
        onSwipeDown: () => setIsBottomNavVisible(false),
      },
      options: { minSwipeDistance: 30 }
    }
  });

  const navigationItems = [
    {
      path: '/',
      label: 'Dashboard',
      icon: HomeIcon,
      exact: true,
    },
    {
      path: '/monitoring',
      label: 'Monitoring',
      icon: ChartBarIcon,
      exact: false,
    },
    {
      path: '/settings',
      label: 'Settings',
      icon: CogIcon,
      exact: false,
    },
  ];

  const isActiveRoute = (path: string, exact: boolean) => {
    if (exact) {
      return location.pathname === path;
    }
    return location.pathname.startsWith(path);
  };

  const toggleMenu = () => {
    setIsMenuOpen(!isMenuOpen);
  };

  const closeMenu = () => {
    setIsMenuOpen(false);
  };

  return (
    <>
      {/* Top Navigation Bar */}
      <nav className={`
        fixed top-0 left-0 right-0 z-50
        bg-design-surface border-b border-design-border shadow-design-sm
        transition-transform duration-design-normal
        ${isBottomNavVisible ? 'translate-y-0' : '-translate-y-full'}
        ${className}
      `}>
        <div className="mobile-header">
          <div className="flex items-center space-x-3">
            <button
              onClick={toggleMenu}
              className="touch-button text-design-text-secondary hover:text-design-text"
              aria-label="Toggle menu"
            >
              {isMenuOpen ? (
                <XMarkIcon className="h-6 w-6" />
              ) : (
                <Bars3Icon className="h-6 w-6" />
              )}
            </button>
            
            <Link
              to="/"
              className="text-lg font-bold text-design-text hover:text-design-text-secondary transition-colors duration-design-fast"
              onClick={closeMenu}
            >
              Health Dashboard
            </Link>
          </div>
          
          <div className="flex items-center space-x-2">
            <ThemeToggle variant="button" />
            <NotificationBell />
          </div>
        </div>
      </nav>

      {/* Mobile Menu Overlay */}
      {isMenuOpen && (
        <div 
          className="fixed inset-0 z-40 bg-black bg-opacity-25"
          onClick={closeMenu}
        />
      )}

      {/* Mobile Menu */}
      <div className={`
        fixed top-16 left-0 right-0 z-40
        bg-design-surface border-b border-design-border shadow-design-lg
        transform transition-transform duration-design-normal
        ${isMenuOpen ? 'translate-y-0' : '-translate-y-full'}
      `}>
        <div className="mobile-container">
          <div className="space-y-1">
            {navigationItems.map((item) => {
              const Icon = item.icon;
              const isActive = isActiveRoute(item.path, item.exact);
              
              return (
                <Link
                  key={item.path}
                  to={item.path}
                  onClick={closeMenu}
                  className={`
                    flex items-center space-x-3 px-3 py-3 rounded-design-md
                    text-design-text font-medium transition-colors duration-design-fast
                    touch-target
                    ${isActive 
                      ? 'bg-design-primary text-design-text-inverse' 
                      : 'hover:bg-design-surface-hover'
                    }
                  `}
                >
                  <Icon className="h-5 w-5" />
                  <span>{item.label}</span>
                </Link>
              );
            })}
          </div>
          
          <div className="mt-4 pt-4 border-t border-design-border">
            <div className="text-sm text-design-text-secondary mb-2">
              Quick Actions
            </div>
            <div className="space-y-1">
              <button
                onClick={() => {
                  // Refresh data
                  window.location.reload();
                }}
                className="
                  w-full flex items-center space-x-3 px-3 py-3 rounded-design-md
                  text-design-text-secondary hover:text-design-text hover:bg-design-surface-hover
                  transition-colors duration-design-fast touch-target
                "
              >
                <ChartBarIcon className="h-5 w-5" />
                <span>Refresh Data</span>
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* Bottom Navigation */}
      <div 
        className={`
          mobile-nav transition-transform duration-design-normal
          ${isBottomNavVisible ? 'translate-y-0' : 'translate-y-full'}
        `}
        {...touchHandlers}
      >
        <div className="flex justify-around">
          {navigationItems.map((item) => {
            const Icon = item.icon;
            const isActive = isActiveRoute(item.path, item.exact);
            
            return (
              <Link
                key={item.path}
                to={item.path}
                className={`
                  mobile-nav-item flex-1
                  ${isActive ? 'active' : ''}
                `}
              >
                <Icon className="h-6 w-6 mb-1" />
                <span>{item.label}</span>
              </Link>
            );
          })}
        </div>
      </div>

      {/* Swipe Indicator */}
      <div className="swipe-indicator left">
        <div className="text-center">
          <div className="text-sm text-design-text-secondary">
            Swipe up to show navigation
          </div>
        </div>
      </div>
    </>
  );
};

import React, { useState, useEffect } from 'react';
import { MobileNavigation } from './MobileNavigation';
import { useThemeAware } from '../contexts/ThemeContext';
import { useTouchGestures } from '../hooks/useTouchGestures';

interface MobileLayoutProps {
  children: React.ReactNode;
  className?: string;
}

export const MobileLayout: React.FC<MobileLayoutProps> = ({ 
  children, 
  className = '' 
}) => {
  const { isDark } = useThemeAware();
  const [isMobile, setIsMobile] = useState(false);
  const [orientation, setOrientation] = useState<'portrait' | 'landscape'>('portrait');

  // Detect mobile device and orientation
  useEffect(() => {
    const checkMobile = () => {
      const isMobileDevice = window.innerWidth <= 768;
      const isPortrait = window.innerHeight > window.innerWidth;
      
      setIsMobile(isMobileDevice);
      setOrientation(isPortrait ? 'portrait' : 'landscape');
    };

    checkMobile();
    window.addEventListener('resize', checkMobile);
    window.addEventListener('orientationchange', checkMobile);

    return () => {
      window.removeEventListener('resize', checkMobile);
      window.removeEventListener('orientationchange', checkMobile);
    };
  }, []);

  // Touch gestures for mobile interactions
  const { touchHandlers } = useTouchGestures({
    swipe: {
      callbacks: {
        onSwipeLeft: () => {
          // Could implement swipe-to-refresh or navigation
          console.log('Swipe left detected');
        },
        onSwipeRight: () => {
          // Could implement swipe-to-go-back
          console.log('Swipe right detected');
        },
      },
      options: { minSwipeDistance: 50 }
    }
  });

  if (!isMobile) {
    // Return desktop layout
    return (
      <div className={`min-h-screen bg-design-background transition-colors duration-design-normal ${className}`}>
        {children}
      </div>
    );
  }

  return (
    <div 
      className={`
        min-h-screen bg-design-background transition-colors duration-design-normal
        mobile-optimized mobile-scroll
        ${orientation === 'landscape' ? 'landscape-mode' : 'portrait-mode'}
        ${className}
      `}
      {...touchHandlers}
    >
      {/* Mobile Navigation */}
      <MobileNavigation />
      
      {/* Main Content Area */}
      <main className="mobile-content pt-16 pb-20">
        <div className="mobile-container">
          {children}
        </div>
      </main>
      
      {/* Mobile-specific styles */}
      <style jsx>{`
        .landscape-mode {
          padding-bottom: 0;
        }
        
        .landscape-mode .mobile-content {
          padding-bottom: 0;
        }
        
        .portrait-mode {
          padding-bottom: 80px;
        }
        
        .portrait-mode .mobile-content {
          padding-bottom: 80px;
        }
        
        /* Ensure content doesn't get hidden behind navigation */
        .mobile-content {
          min-height: calc(100vh - 64px - 80px);
        }
        
        .landscape-mode .mobile-content {
          min-height: calc(100vh - 64px);
        }
        
        /* Smooth scrolling for mobile */
        .mobile-scroll {
          -webkit-overflow-scrolling: touch;
          scroll-behavior: smooth;
        }
        
        /* Prevent zoom on input focus */
        input, textarea, select {
          font-size: 16px;
        }
        
        /* Mobile-specific touch targets */
        button, a, [role="button"] {
          min-height: 44px;
          min-width: 44px;
        }
        
        /* Mobile-optimized spacing */
        .mobile-container > * + * {
          margin-top: 1rem;
        }
        
        /* Mobile card spacing */
        .mobile-card + .mobile-card {
          margin-top: 1rem;
        }
      `}</style>
    </div>
  );
};

// Mobile-specific utility components
export const MobileCard: React.FC<{
  children: React.ReactNode;
  className?: string;
  onClick?: () => void;
}> = ({ children, className = '', onClick }) => {
  return (
    <div 
      className={`
        mobile-card gesture-feedback
        ${onClick ? 'cursor-pointer hover:shadow-design-lg' : ''}
        ${className}
      `}
      onClick={onClick}
    >
      {children}
    </div>
  );
};

export const MobileSection: React.FC<{
  title: string;
  children: React.ReactNode;
  className?: string;
}> = ({ title, children, className = '' }) => {
  return (
    <section className={`mobile-card ${className}`}>
      <h2 className="text-lg font-semibold text-design-text mb-4">{title}</h2>
      {children}
    </section>
  );
};

export const MobileButton: React.FC<{
  children: React.ReactNode;
  onClick?: () => void;
  variant?: 'primary' | 'secondary' | 'danger';
  size?: 'sm' | 'md' | 'lg';
  disabled?: boolean;
  className?: string;
}> = ({ 
  children, 
  onClick, 
  variant = 'primary', 
  size = 'md', 
  disabled = false,
  className = '' 
}) => {
  const baseClasses = 'touch-button font-medium transition-all duration-design-fast';
  
  const variantClasses = {
    primary: 'bg-design-primary text-design-text-inverse hover:bg-design-primary-hover shadow-design-sm',
    secondary: 'bg-design-secondary text-design-text-inverse hover:bg-design-secondary-hover shadow-design-sm',
    danger: 'bg-design-error text-design-text-inverse hover:bg-design-error-hover shadow-design-sm',
  };
  
  const sizeClasses = {
    sm: 'px-3 py-2 text-sm',
    md: 'px-4 py-3 text-base',
    lg: 'px-6 py-4 text-lg',
  };
  
  const disabledClasses = disabled 
    ? 'opacity-50 cursor-not-allowed' 
    : 'active:scale-95';
  
  return (
    <button
      onClick={onClick}
      disabled={disabled}
      className={`
        ${baseClasses}
        ${variantClasses[variant]}
        ${sizeClasses[size]}
        ${disabledClasses}
        ${className}
      `}
    >
      {children}
    </button>
  );
};

export const MobileInput: React.FC<{
  label?: string;
  placeholder?: string;
  value?: string;
  onChange?: (value: string) => void;
  type?: 'text' | 'email' | 'password' | 'number';
  error?: string;
  className?: string;
}> = ({ 
  label, 
  placeholder, 
  value, 
  onChange, 
  type = 'text', 
  error,
  className = '' 
}) => {
  return (
    <div className={`mobile-card ${className}`}>
      {label && (
        <label className="block text-sm font-medium text-design-text mb-2">
          {label}
        </label>
      )}
      <input
        type={type}
        placeholder={placeholder}
        value={value}
        onChange={(e) => onChange?.(e.target.value)}
        className={`
          w-full px-3 py-3 border border-design-border rounded-design-md
          bg-design-surface text-design-text text-base
          focus:outline-none focus:ring-2 focus:ring-design-border-focus focus:border-design-border-focus
          transition-colors duration-design-fast
          ${error ? 'border-design-error' : ''}
        `}
      />
      {error && (
        <p className="mt-1 text-sm text-design-error">{error}</p>
      )}
    </div>
  );
};

export const MobileGrid: React.FC<{
  children: React.ReactNode;
  columns?: 1 | 2;
  gap?: 'sm' | 'md' | 'lg';
  className?: string;
}> = ({ children, columns = 1, gap = 'md', className = '' }) => {
  const gapClasses = {
    sm: 'gap-2',
    md: 'gap-4',
    lg: 'gap-6',
  };
  
  const gridClasses = columns === 2 ? 'grid-cols-2' : 'grid-cols-1';
  
  return (
    <div className={`
      grid ${gridClasses} ${gapClasses[gap]}
      ${className}
    `}>
      {children}
    </div>
  );
};
